import asyncio
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.base import AsyncSessionLocal, engine
from app.models.tenant import Tenant
from app.models.user import User
from app.models.msme import MSME
from app.models.financial_data import FinancialData
from app.models.digital_twin import DigitalTwin
from app.models.ews_alert import EWSAlert
from app.models.risk_prediction import RiskPrediction
from app.core.security import hash_password, encrypt_field

async def seed():
    async with AsyncSessionLocal() as db:
        # Check if Tenant already exists
        result = await db.execute(select(Tenant).where(Tenant.code == "IDBI"))
        tenant = result.scalars().first()
        if not tenant:
            tenant = Tenant(
                id=uuid.uuid4(),
                name="IDBI Bank",
                code="IDBI",
                settings={}
            )
            db.add(tenant)
            await db.flush()
            print("Tenant created")

        # Check if User already exists
        result = await db.execute(select(User).where(User.email == "vedant@bank.com"))
        user = result.scalars().first()
        if not user:
            user = User(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                email="vedant@bank.com",
                password_hash=hash_password("password"),
                first_name="Vedant",
                last_name="Kolsure",
                role="RISK_MANAGER",
                is_active=True
            )
            db.add(user)
            await db.flush()
            print("User created")

        # Clear existing seed data if any
        # (in case we run this multiple times)
        await db.execute(select(MSME))
        # Add MSMEs
        result = await db.execute(select(MSME).where(MSME.business_name == "Shree Ganesh Traders"))
        msme1 = result.scalars().first()
        if not msme1:
            msme1 = MSME(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                created_by=user.id,
                assigned_officer=user.id,
                business_name="Shree Ganesh Traders",
                gstin=encrypt_field("27ABCDE1234F1Z5"),
                pan=encrypt_field("ABCDE1234F"),
                industry_type="Wholesale Trade",
                sub_industry="Agro Commodities",
                state="Maharashtra",
                district="Pune",
                city="Pune",
                registration_date=date(2018, 5, 12),
                status="ACTIVE",
                risk_tier="High",
                msme_category="Medium",
                annual_turnover=Decimal("125300000.00"),
                latest_risk_score=Decimal("82.00"),
                latest_ews_score=Decimal("85.00")
            )
            db.add(msme1)
            await db.flush()
            print("MSME 1 created")

            # Create FinancialData
            fin = FinancialData(
                id=uuid.uuid4(),
                msme_id=msme1.id,
                fiscal_year=2026,
                fiscal_quarter=1,
                revenue=Decimal("37200000.00"),
                net_profit=Decimal("1860000.00"),
                current_assets=Decimal("12400000.00"),
                current_liabilities=Decimal("10000000.00"),
                current_ratio=Decimal("1.24"),
                debt_to_equity=Decimal("2.35"),
                free_cashflow=Decimal("1240000.00"),
                interest_coverage=Decimal("1.08")
            )
            db.add(fin)

            # Create DigitalTwin
            twin = DigitalTwin(
                id=uuid.uuid4(),
                msme_id=msme1.id,
                version=1,
                health_score=Decimal("62.00"),
                growth_trend_index=Decimal("40.00"),
                risk_index=Decimal("82.00"),
                liquidity_score=Decimal("55.00"),
                profitability_score=Decimal("45.00"),
                solvency_score=Decimal("38.00"),
                compliance_score=Decimal("90.00"),
                status="active",
                narrative_summary="The MSME is showing signs of financial stress. Monitor closely.",
                generated_at=datetime.now(timezone.utc),
                cashflow_12m={},
                peer_group_id="Wholesale Traders"
            )
            db.add(twin)
            await db.flush()

            msme1.latest_twin_id = twin.id

            # Create RiskPrediction
            pred = RiskPrediction(
                id=uuid.uuid4(),
                msme_id=msme1.id,
                twin_id=twin.id,
                risk_score=Decimal("82.00"),
                probability_of_default=Decimal("0.1260"),
                recovery_probability=Decimal("0.4500"),
                confidence_score=Decimal("0.8700"),
                risk_tier="High",
                model_version="1.0.0",
                predicted_at=datetime.now(timezone.utc),
                top_risk_factors={
                    "Declining Revenue": "Impact: High",
                    "High Debt to Equity": "Impact: High",
                    "Low Cash Flow": "Impact: Medium",
                    "Working Capital Gap": "Impact: Medium"
                }
            )
            db.add(pred)

            # Create EWS Alert
            alert = EWSAlert(
                id=uuid.uuid4(),
                msme_id=msme1.id,
                tenant_id=tenant.id,
                alert_code="REV_DECLINE",
                alert_type="Financial",
                severity="HIGH",
                ews_score=Decimal("85.00"),
                title="Declining Revenue Trend",
                reason="Revenue has shown a downward trend of 15.4% in the last quarter.",
                default_probability_30d=Decimal("0.1260"),
                recommended_action="Review with Conditions",
                is_acknowledged=False
            )
            db.add(alert)
            print("MSME 1 support data created")

        # Create other MSMEs for Top Risky list
        risky_msmes = [
            ("Kartik Manufacturing", Decimal("76.00"), "Manufacturing", "Gujarat"),
            ("Maa Enterprises", Decimal("68.00"), "Services", "Delhi"),
            ("Om Sai Textiles", Decimal("65.00"), "Textiles", "Tamil Nadu"),
            ("Vishwakarma Engineers", Decimal("62.00"), "Engineering", "Karnataka")
        ]
        for name, score, ind, state in risky_msmes:
            result = await db.execute(select(MSME).where(MSME.business_name == name))
            if not result.scalars().first():
                m = MSME(
                    id=uuid.uuid4(),
                    tenant_id=tenant.id,
                    created_by=user.id,
                    assigned_officer=user.id,
                    business_name=name,
                    gstin=encrypt_field("27GSTINXXXXXX"),
                    pan=encrypt_field("PANXXXXXX"),
                    industry_type=ind,
                    state=state,
                    status="ACTIVE",
                    risk_tier="High" if score >= 70 else "Medium",
                    latest_risk_score=score,
                    latest_ews_score=score + 3
                )
                db.add(m)

                # Create EWS Alert for other MSMEs to reach 7 alert count
                alert = EWSAlert(
                    id=uuid.uuid4(),
                    msme_id=m.id,
                    tenant_id=tenant.id,
                    alert_code="EWS_GENERIC",
                    alert_type="Financial",
                    severity="HIGH" if score >= 70 else "MEDIUM",
                    ews_score=score + 3,
                    title="Risk Alert - " + name,
                    reason="Automated Early Warning trigger based on recent industry index volatility.",
                    is_acknowledged=False
                )
                db.add(alert)

        await db.commit()
        print("Database seeded successfully!")

if __name__ == "__main__":
    asyncio.run(seed())
