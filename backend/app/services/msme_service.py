"""
FinTwin AI — MSME Service
Business logic for MSME profile management.
"""

from __future__ import annotations

from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, TenantIsolationError
from app.core.security import decrypt_field, encrypt_field
from app.models.msme import MSME
from app.repositories.msme_repository import MSMERepository
from app.schemas.common import PaginatedResponse
from app.schemas.msme import MSMECreate, MSMEListResponse, MSMEResponse, MSMEUpdate
from app.schemas.user import CurrentUser

logger = structlog.get_logger(__name__)


class MSMEService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = MSMERepository(db)

    async def create(self, data: MSMECreate, current_user: CurrentUser) -> MSMEResponse:
        """Create a new MSME profile with encrypted PII."""
        # Check for duplicate GSTIN
        existing = await self.repo.get_by_gstin(
            encrypt_field(data.gstin), current_user.tenant_id
        )
        if existing:
            raise ConflictError(f"MSME with GSTIN '{data.gstin}' already exists")

        msme_data = data.model_dump()
        msme_data["tenant_id"] = current_user.tenant_id
        msme_data["created_by"] = current_user.id
        # Encrypt PII fields
        msme_data["gstin"] = encrypt_field(data.gstin)
        msme_data["pan"] = encrypt_field(data.pan)

        msme = await self.repo.create(msme_data)
        logger.info("MSME created", msme_id=str(msme.id), tenant_id=current_user.tenant_id)

        # Log audit event
        await self._audit_log(current_user, "CREATE", msme)

        return self._to_response(msme)

    async def get_by_id(self, msme_id: UUID, tenant_id: str) -> MSMEResponse:
        """Get MSME by ID with tenant isolation check."""
        msme = await self.repo.get(msme_id)
        if not msme or msme.deleted_at:
            raise NotFoundError("MSME", str(msme_id))
        if str(msme.tenant_id) != str(tenant_id):
            raise TenantIsolationError()
        return self._to_response(msme)

    async def update(
        self, msme_id: UUID, data: MSMEUpdate, current_user: CurrentUser
    ) -> MSMEResponse:
        """Update MSME fields."""
        msme = await self.repo.get(msme_id)
        if not msme or msme.deleted_at:
            raise NotFoundError("MSME", str(msme_id))
        if str(msme.tenant_id) != current_user.tenant_id:
            raise TenantIsolationError()

        update_data = data.model_dump(exclude_unset=True)
        updated = await self.repo.update(msme_id, update_data)
        await self._audit_log(current_user, "UPDATE", updated)
        return self._to_response(updated)

    async def soft_delete(
        self, msme_id: UUID, current_user: CurrentUser
    ) -> None:
        """Soft-delete an MSME."""
        success = await self.repo.soft_delete(msme_id, current_user.tenant_id)
        if not success:
            raise NotFoundError("MSME", str(msme_id))
        await self._audit_log(current_user, "DELETE", None, entity_id=str(msme_id))

    async def search(
        self,
        tenant_id: str,
        current_user: CurrentUser,
        query: str | None,
        industry_type: str | None,
        state: str | None,
        risk_tier: str | None,
        status: str | None,
        limit: int,
        offset: int,
    ) -> PaginatedResponse[MSMEListResponse]:
        """Search MSMEs with filters. Applies regional scoping for Regional Managers."""
        # Regional Manager: scope to their region (state)
        effective_state = state
        if current_user.role == "REGIONAL_MANAGER" and current_user.region:
            effective_state = current_user.region

        items, total = await self.repo.search(
            tenant_id=UUID(tenant_id),
            query=query,
            industry_type=industry_type,
            state=effective_state,
            risk_tier=risk_tier,
            status=status,
            limit=limit,
            offset=offset,
        )
        responses = [self._to_list_response(m) for m in items]
        return PaginatedResponse.create(responses, total, limit, offset)

    async def get_completeness_report(
        self, msme_id: UUID, tenant_id: str
    ) -> dict:
        """Get data completeness score and breakdown of what is missing."""
        msme = await self.repo.get(msme_id)
        if not msme or str(msme.tenant_id) != tenant_id:
            raise NotFoundError("MSME", str(msme_id))

        from sqlalchemy import select, func
        from app.models.financial_data import FinancialData, GSTData, CreditData, BankTransaction

        fin_count_result = await self.db.execute(
            select(func.count()).select_from(FinancialData).where(
                FinancialData.msme_id == msme_id
            )
        )
        gst_count_result = await self.db.execute(
            select(func.count()).select_from(GSTData).where(GSTData.msme_id == msme_id)
        )
        credit_count_result = await self.db.execute(
            select(func.count()).select_from(CreditData).where(CreditData.msme_id == msme_id)
        )
        txn_count_result = await self.db.execute(
            select(func.count()).select_from(BankTransaction).where(
                BankTransaction.msme_id == msme_id
            )
        )

        return {
            "overall_completeness": msme.data_completeness,
            "sections": {
                "financial_data": {
                    "present": fin_count_result.scalar_one() > 0,
                    "records": fin_count_result.scalar_one(),
                    "max_weight": 40,
                },
                "gst_data": {
                    "present": gst_count_result.scalar_one() > 0,
                    "records": gst_count_result.scalar_one(),
                    "max_weight": 20,
                },
                "credit_data": {
                    "present": credit_count_result.scalar_one() > 0,
                    "records": credit_count_result.scalar_one(),
                    "max_weight": 20,
                },
                "bank_transactions": {
                    "present": txn_count_result.scalar_one() > 0,
                    "records": txn_count_result.scalar_one(),
                    "max_weight": 20,
                },
            },
            "ready_for_evaluation": msme.data_completeness >= 70,
        }

    async def get_timeline(self, msme_id: UUID, tenant_id: str, limit: int) -> list[dict]:
        """Get chronological activity timeline for an MSME."""
        from sqlalchemy import select, union_all, literal
        from app.models.audit_log import AuditLog

        result = await self.db.execute(
            select(AuditLog)
            .where(AuditLog.entity_id == msme_id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )
        logs = result.scalars().all()
        return [
            {
                "id": str(log.id),
                "event": log.action,
                "entity_type": log.entity_type,
                "description": log.description,
                "user_id": str(log.user_id) if log.user_id else None,
                "timestamp": log.created_at.isoformat(),
            }
            for log in logs
        ]

    def _to_response(self, msme: MSME) -> MSMEResponse:
        data = msme.__dict__.copy()
        # Decrypt PII for response
        data["gstin"] = decrypt_field(data.get("gstin", ""))
        data["pan"] = decrypt_field(data.get("pan", ""))
        return MSMEResponse.model_validate(data)

    def _to_list_response(self, msme: MSME) -> MSMEListResponse:
        data = msme.__dict__.copy()
        data["gstin"] = decrypt_field(data.get("gstin", ""))
        return MSMEListResponse.model_validate(data)

    async def _audit_log(
        self,
        current_user: CurrentUser,
        action: str,
        msme: MSME | None,
        entity_id: str | None = None,
    ) -> None:
        from app.models.audit_log import AuditLog
        import uuid
        eid = uuid.UUID(entity_id) if entity_id else (msme.id if msme else None)
        log = AuditLog(
            tenant_id=uuid.UUID(current_user.tenant_id),
            user_id=uuid.UUID(current_user.id),
            entity_type="MSME",
            entity_id=eid,
            action=action,
            description=f"MSME {action.lower()}",
        )
        self.db.add(log)
        await self.db.flush()
