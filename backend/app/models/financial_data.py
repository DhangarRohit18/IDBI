from __future__ import annotations
import uuid
from decimal import Decimal
from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base_model import BaseModel


class FinancialData(BaseModel):
    __tablename__ = "financial_data"
    __table_args__ = (UniqueConstraint("msme_id", "fiscal_year", "fiscal_quarter"),)

    msme_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("msmes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    fiscal_year: Mapped[int] = mapped_column(Integer, nullable=False)
    fiscal_quarter: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Income Statement
    revenue: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    cost_of_goods_sold: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    gross_profit: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    operating_expenses: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    ebitda: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    depreciation: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    ebit: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    interest_expense: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    tax: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    net_profit: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))

    # Balance Sheet - Assets
    total_assets: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    current_assets: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    cash_and_equivalents: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    accounts_receivable: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    inventory: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    fixed_assets: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))

    # Balance Sheet - Liabilities
    total_liabilities: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    current_liabilities: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    accounts_payable: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    short_term_debt: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    long_term_debt: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    equity: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    retained_earnings: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))

    # Cash Flow
    operating_cashflow: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    investing_cashflow: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    financing_cashflow: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    free_cashflow: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    capex: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))

    # Computed Ratios
    current_ratio: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    quick_ratio: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    debt_to_equity: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    interest_coverage: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    return_on_assets: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    return_on_equity: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    net_profit_margin: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    asset_turnover: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))

    # Metadata
    source: Mapped[str] = mapped_column(String(50), default="MANUAL")
    document_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    is_audited: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text)

    # Relationships
    msme: Mapped["MSME"] = relationship("MSME", back_populates="financial_data", lazy="noload")


class GSTData(BaseModel):
    __tablename__ = "gst_data"
    __table_args__ = (UniqueConstraint("msme_id", "return_type", "filing_period"),)

    msme_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("msmes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    gstin: Mapped[str] = mapped_column(String(15), nullable=False)
    return_type: Mapped[str] = mapped_column(String(20), nullable=False)
    filing_period: Mapped[str] = mapped_column(String(10), nullable=False)  # Stored as YYYY-MM-DD
    taxable_turnover: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    igst_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    cgst_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    sgst_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    total_tax: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    filing_status: Mapped[str] = mapped_column(String(20), nullable=False, default="NOT_FILED")
    due_date: Mapped[str | None] = mapped_column(String(10))
    filed_date: Mapped[str | None] = mapped_column(String(10))
    late_fee: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    source: Mapped[str] = mapped_column(String(50), default="GSTN_API")

    # Relationships
    msme: Mapped["MSME"] = relationship("MSME", back_populates="gst_data", lazy="noload")


class CreditData(BaseModel):
    __tablename__ = "credit_data"

    msme_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("msmes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    bureau_name: Mapped[str] = mapped_column(String(50), nullable=False)
    credit_score: Mapped[int] = mapped_column(Integer, nullable=False)
    credit_rank: Mapped[str | None] = mapped_column(String(10))
    outstanding_loans: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    total_credit_limit: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    credit_utilization: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    existing_loan_count: Mapped[int] = mapped_column(Integer, default=0)
    dpd_30: Mapped[int] = mapped_column(Integer, default=0)
    dpd_60: Mapped[int] = mapped_column(Integer, default=0)
    dpd_90: Mapped[int] = mapped_column(Integer, default=0)
    credit_history_months: Mapped[int | None] = mapped_column(Integer)
    oldest_account_date: Mapped[str | None] = mapped_column(String(10))
    recent_enquiries: Mapped[int] = mapped_column(Integer, default=0)
    credit_rating: Mapped[str | None] = mapped_column(String(5))
    report_reference: Mapped[str | None] = mapped_column(String(100))
    as_of_date: Mapped[str] = mapped_column(String(10), nullable=False)

    # Relationships
    msme: Mapped["MSME"] = relationship("MSME", back_populates="credit_data", lazy="noload")


class BankTransaction(BaseModel):
    __tablename__ = "bank_transactions"

    msme_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("msmes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    account_number: Mapped[str | None] = mapped_column(String(20))
    ifsc_code: Mapped[str | None] = mapped_column(String(11))
    txn_date: Mapped[str] = mapped_column(String(10), nullable=False)
    value_date: Mapped[str | None] = mapped_column(String(10))
    txn_type: Mapped[str] = mapped_column(String(20), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    balance: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    description: Mapped[str | None] = mapped_column(Text)
    counterparty: Mapped[str | None] = mapped_column(String(200))
    category: Mapped[str | None] = mapped_column(String(100))
    reference_no: Mapped[str | None] = mapped_column(String(100))
    document_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    # Relationships
    msme: Mapped["MSME"] = relationship("MSME", back_populates="transactions", lazy="noload")
