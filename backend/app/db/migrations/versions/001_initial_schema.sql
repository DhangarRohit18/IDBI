-- =============================================================================
-- FinTwin AI — Complete PostgreSQL Database Schema
-- Version: 1.0.0
-- =============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For fuzzy text search

-- =============================================================================
-- ENUMS
-- =============================================================================

CREATE TYPE user_role AS ENUM (
    'BANK_ADMIN',
    'LOAN_OFFICER',
    'RISK_MANAGER',
    'CREDIT_ANALYST',
    'REGIONAL_MANAGER'
);

CREATE TYPE msme_status AS ENUM (
    'DRAFT',
    'ACTIVE',
    'UNDER_REVIEW',
    'SUSPENDED',
    'CLOSED'
);

CREATE TYPE msme_category AS ENUM (
    'MICRO',
    'SMALL',
    'MEDIUM'
);

CREATE TYPE risk_tier AS ENUM (
    'VERY_LOW',
    'LOW',
    'MEDIUM',
    'HIGH',
    'VERY_HIGH'
);

CREATE TYPE loan_recommendation AS ENUM (
    'APPROVE',
    'REJECT',
    'REVIEW',
    'REDUCE_LOAN',
    'INCREASE_COLLATERAL',
    'RESTRUCTURE_EMI'
);

CREATE TYPE loan_status AS ENUM (
    'PENDING',
    'PROCESSING',
    'COMPLETED',
    'APPROVED',
    'REJECTED',
    'DISBURSED',
    'CLOSED'
);

CREATE TYPE evaluation_status AS ENUM (
    'DRAFT',
    'PROCESSING',
    'COMPLETED',
    'CANCELLED'
);

CREATE TYPE alert_severity AS ENUM (
    'INFO',
    'WARNING',
    'CRITICAL'
);

CREATE TYPE document_type AS ENUM (
    'BALANCE_SHEET',
    'PROFIT_LOSS',
    'BANK_STATEMENT',
    'GST_RETURN',
    'ITR',
    'AUDIT_REPORT',
    'INCORPORATION_CERT',
    'KYC_DOCUMENT',
    'COLLATERAL_DOCUMENT',
    'OTHER'
);

CREATE TYPE document_status AS ENUM (
    'UPLOADED',
    'PROCESSING',
    'PROCESSED',
    'FAILED'
);

CREATE TYPE twin_status AS ENUM (
    'GENERATING',
    'ACTIVE',
    'STALE',
    'FAILED'
);

CREATE TYPE agent_pipeline_status AS ENUM (
    'QUEUED',
    'RUNNING',
    'COMPLETED',
    'FAILED',
    'PARTIAL'
);

CREATE TYPE report_type AS ENUM (
    'MSME_RISK_REPORT',
    'PORTFOLIO_SUMMARY',
    'EWS_ALERT_REPORT',
    'EVALUATION_REPORT',
    'AUDIT_REPORT'
);

CREATE TYPE report_format AS ENUM ('PDF', 'EXCEL', 'CSV');

CREATE TYPE report_status AS ENUM ('PENDING', 'GENERATING', 'COMPLETED', 'FAILED');

CREATE TYPE scenario_type AS ENUM (
    'REVENUE_DROP',
    'INFLATION',
    'INTEREST_RATE_INCREASE',
    'DELAYED_PAYMENTS',
    'SUPPLIER_FAILURE',
    'PANDEMIC',
    'COMPOUND'
);

CREATE TYPE gst_filing_status AS ENUM (
    'FILED',
    'NOT_FILED',
    'LATE_FILED',
    'CANCELLED'
);

CREATE TYPE notification_type AS ENUM (
    'EWS_ALERT',
    'EVALUATION_COMPLETE',
    'DIGITAL_TWIN_UPDATED',
    'DOCUMENT_PROCESSED',
    'LOAN_DECISION',
    'SYSTEM_ALERT',
    'REPORT_READY'
);

-- =============================================================================
-- TABLE: tenants
-- =============================================================================
CREATE TABLE tenants (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            VARCHAR(200) NOT NULL,
    code            VARCHAR(20) NOT NULL UNIQUE,
    logo_url        TEXT,
    primary_color   VARCHAR(7) DEFAULT '#1a56db',
    settings        JSONB NOT NULL DEFAULT '{}',
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE tenants IS 'Multi-tenant bank organizations using FinTwin AI';

-- =============================================================================
-- TABLE: users
-- =============================================================================
CREATE TABLE users (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id               UUID NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    email                   VARCHAR(255) NOT NULL,
    password_hash           VARCHAR(255) NOT NULL,
    first_name              VARCHAR(100) NOT NULL,
    last_name               VARCHAR(100) NOT NULL,
    role                    user_role NOT NULL,
    phone                   VARCHAR(15),
    employee_id             VARCHAR(50),
    department              VARCHAR(100),
    region                  VARCHAR(100),           -- For Regional Manager filtering
    mfa_enabled             BOOLEAN NOT NULL DEFAULT FALSE,
    mfa_secret              TEXT,                   -- Encrypted TOTP secret
    avatar_url              TEXT,
    is_active               BOOLEAN NOT NULL DEFAULT TRUE,
    failed_login_attempts   INTEGER NOT NULL DEFAULT 0,
    locked_until            TIMESTAMPTZ,
    password_changed_at     TIMESTAMPTZ,
    last_login_at           TIMESTAMPTZ,
    last_login_ip           INET,
    created_by              UUID REFERENCES users(id),
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(tenant_id, email)
);

CREATE INDEX idx_users_tenant ON users(tenant_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(tenant_id, role);

COMMENT ON TABLE users IS 'Platform users with role-based access control';

-- =============================================================================
-- TABLE: refresh_tokens
-- =============================================================================
CREATE TABLE refresh_tokens (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash  VARCHAR(255) NOT NULL UNIQUE,
    device_id   VARCHAR(255),
    user_agent  TEXT,
    ip_address  INET,
    is_revoked  BOOLEAN NOT NULL DEFAULT FALSE,
    expires_at  TIMESTAMPTZ NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_refresh_tokens_user ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_hash ON refresh_tokens(token_hash);

-- =============================================================================
-- TABLE: msmes
-- =============================================================================
CREATE TABLE msmes (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id               UUID NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    created_by              UUID NOT NULL REFERENCES users(id),
    assigned_officer        UUID REFERENCES users(id),
    
    -- Business Identity
    business_name           VARCHAR(200) NOT NULL,
    gstin                   VARCHAR(15) NOT NULL,      -- Encrypted at application level
    pan                     VARCHAR(10) NOT NULL,       -- Encrypted at application level
    industry_type           VARCHAR(100) NOT NULL,
    sub_industry            VARCHAR(100),
    business_description    TEXT,
    
    -- Location
    state                   VARCHAR(100) NOT NULL,
    district                VARCHAR(100),
    city                    VARCHAR(100),
    pincode                 VARCHAR(6),
    address                 TEXT,
    
    -- Registration
    registration_date       DATE NOT NULL,
    registration_number     VARCHAR(50),
    
    -- Contact
    email                   VARCHAR(255),
    phone                   VARCHAR(15),
    website                 VARCHAR(255),
    
    -- Financial Classification
    msme_category           msme_category,
    annual_turnover         NUMERIC(18, 2),
    
    -- Status
    status                  msme_status NOT NULL DEFAULT 'DRAFT',
    risk_tier               risk_tier,
    
    -- AI Generated Fields
    data_completeness       INTEGER NOT NULL DEFAULT 0 CHECK (data_completeness BETWEEN 0 AND 100),
    latest_twin_id          UUID,                       -- FK added after digital_twins table
    latest_risk_score       NUMERIC(6, 2),
    latest_ews_score        NUMERIC(6, 2),
    
    -- Metadata
    tags                    TEXT[],
    notes                   TEXT,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at              TIMESTAMPTZ,                -- Soft delete
    
    UNIQUE(tenant_id, gstin),
    CONSTRAINT chk_risk_score CHECK (latest_risk_score IS NULL OR latest_risk_score BETWEEN 0 AND 1000)
);

CREATE INDEX idx_msmes_tenant ON msmes(tenant_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_msmes_gstin ON msmes(gstin);
CREATE INDEX idx_msmes_status ON msmes(status, tenant_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_msmes_risk_tier ON msmes(risk_tier, tenant_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_msmes_state ON msmes(state, tenant_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_msmes_industry ON msmes(industry_type, tenant_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_msmes_officer ON msmes(assigned_officer) WHERE deleted_at IS NULL;
CREATE INDEX idx_msmes_name_trgm ON msmes USING GIN(business_name gin_trgm_ops);

COMMENT ON TABLE msmes IS 'MSME business profiles — core entity for all AI analysis';

-- =============================================================================
-- TABLE: financial_data
-- =============================================================================
CREATE TABLE financial_data (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    msme_id                 UUID NOT NULL REFERENCES msmes(id) ON DELETE CASCADE,
    fiscal_year             INTEGER NOT NULL CHECK (fiscal_year BETWEEN 2000 AND 2100),
    fiscal_quarter          INTEGER CHECK (fiscal_quarter BETWEEN 1 AND 4),
    
    -- Income Statement
    revenue                 NUMERIC(18, 2),
    cost_of_goods_sold      NUMERIC(18, 2),
    gross_profit            NUMERIC(18, 2),
    operating_expenses      NUMERIC(18, 2),
    ebitda                  NUMERIC(18, 2),
    depreciation            NUMERIC(18, 2),
    ebit                    NUMERIC(18, 2),
    interest_expense        NUMERIC(18, 2),
    tax                     NUMERIC(18, 2),
    net_profit              NUMERIC(18, 2),
    
    -- Balance Sheet — Assets
    total_assets            NUMERIC(18, 2),
    current_assets          NUMERIC(18, 2),
    cash_and_equivalents    NUMERIC(18, 2),
    accounts_receivable     NUMERIC(18, 2),
    inventory               NUMERIC(18, 2),
    fixed_assets            NUMERIC(18, 2),
    
    -- Balance Sheet — Liabilities
    total_liabilities       NUMERIC(18, 2),
    current_liabilities     NUMERIC(18, 2),
    accounts_payable        NUMERIC(18, 2),
    short_term_debt         NUMERIC(18, 2),
    long_term_debt          NUMERIC(18, 2),
    
    -- Equity
    equity                  NUMERIC(18, 2),
    retained_earnings       NUMERIC(18, 2),
    
    -- Cash Flow
    operating_cashflow      NUMERIC(18, 2),
    investing_cashflow      NUMERIC(18, 2),
    financing_cashflow      NUMERIC(18, 2),
    free_cashflow           NUMERIC(18, 2),
    capex                   NUMERIC(18, 2),
    
    -- Computed Ratios (stored for performance)
    current_ratio           NUMERIC(10, 4),
    quick_ratio             NUMERIC(10, 4),
    debt_to_equity          NUMERIC(10, 4),
    interest_coverage       NUMERIC(10, 4),
    return_on_assets        NUMERIC(10, 4),
    return_on_equity        NUMERIC(10, 4),
    net_profit_margin       NUMERIC(10, 4),
    asset_turnover          NUMERIC(10, 4),
    
    -- Metadata
    source                  VARCHAR(50) DEFAULT 'MANUAL',  -- MANUAL, CSV, API, OCR
    document_id             UUID,
    is_audited              BOOLEAN DEFAULT FALSE,
    notes                   TEXT,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    UNIQUE(msme_id, fiscal_year, fiscal_quarter)
);

CREATE INDEX idx_financial_data_msme ON financial_data(msme_id, fiscal_year DESC);

COMMENT ON TABLE financial_data IS 'Annual and quarterly financial statements per MSME';

-- =============================================================================
-- TABLE: gst_data
-- =============================================================================
CREATE TABLE gst_data (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    msme_id                 UUID NOT NULL REFERENCES msmes(id) ON DELETE CASCADE,
    gstin                   VARCHAR(15) NOT NULL,
    return_type             VARCHAR(20) NOT NULL,       -- GSTR1, GSTR3B, etc.
    filing_period           DATE NOT NULL,              -- First day of period
    taxable_turnover        NUMERIC(18, 2),
    igst_amount             NUMERIC(18, 2),
    cgst_amount             NUMERIC(18, 2),
    sgst_amount             NUMERIC(18, 2),
    total_tax               NUMERIC(18, 2),
    filing_status           gst_filing_status NOT NULL DEFAULT 'NOT_FILED',
    due_date                DATE,
    filed_date              DATE,
    is_late                 BOOLEAN GENERATED ALWAYS AS (
                                filed_date IS NOT NULL AND due_date IS NOT NULL AND filed_date > due_date
                            ) STORED,
    late_fee                NUMERIC(10, 2),
    source                  VARCHAR(50) DEFAULT 'GSTN_API',
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    UNIQUE(msme_id, return_type, filing_period)
);

CREATE INDEX idx_gst_data_msme ON gst_data(msme_id, filing_period DESC);
CREATE INDEX idx_gst_data_status ON gst_data(msme_id, filing_status);

-- =============================================================================
-- TABLE: credit_data
-- =============================================================================
CREATE TABLE credit_data (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    msme_id                 UUID NOT NULL REFERENCES msmes(id) ON DELETE CASCADE,
    bureau_name             VARCHAR(50) NOT NULL,       -- CIBIL, EXPERIAN, CRIF
    credit_score            INTEGER NOT NULL CHECK (credit_score BETWEEN 300 AND 900),
    credit_rank             VARCHAR(10),
    
    -- Outstanding Obligations
    outstanding_loans       NUMERIC(18, 2),
    total_credit_limit      NUMERIC(18, 2),
    credit_utilization      NUMERIC(5, 2),
    existing_loan_count     INTEGER DEFAULT 0,
    
    -- Delinquency
    dpd_30                  INTEGER DEFAULT 0,          -- Days Past Due 30
    dpd_60                  INTEGER DEFAULT 0,
    dpd_90                  INTEGER DEFAULT 0,
    
    -- History
    credit_history_months   INTEGER,
    oldest_account_date     DATE,
    recent_enquiries        INTEGER DEFAULT 0,
    
    -- Assessment
    credit_rating           VARCHAR(5),                 -- AAA, AA, A, BBB, etc.
    report_reference        VARCHAR(100),
    as_of_date              DATE NOT NULL,
    
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_credit_data_msme ON credit_data(msme_id, as_of_date DESC);

-- =============================================================================
-- TABLE: bank_transactions
-- =============================================================================
CREATE TABLE bank_transactions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    msme_id         UUID NOT NULL REFERENCES msmes(id) ON DELETE CASCADE,
    account_number  VARCHAR(20),
    ifsc_code       VARCHAR(11),
    txn_date        DATE NOT NULL,
    value_date      DATE,
    txn_type        VARCHAR(20) NOT NULL,               -- CREDIT, DEBIT
    amount          NUMERIC(18, 2) NOT NULL,
    balance         NUMERIC(18, 2),
    description     TEXT,
    counterparty    VARCHAR(200),
    category        VARCHAR(100),                       -- SALES, PURCHASE, LOAN_EMI, etc.
    reference_no    VARCHAR(100),
    document_id     UUID,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_transactions_msme_date ON bank_transactions(msme_id, txn_date DESC);
CREATE INDEX idx_transactions_category ON bank_transactions(msme_id, category);

-- =============================================================================
-- TABLE: documents
-- =============================================================================
CREATE TABLE documents (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    msme_id         UUID NOT NULL REFERENCES msmes(id) ON DELETE CASCADE,
    uploaded_by     UUID NOT NULL REFERENCES users(id),
    document_type   document_type NOT NULL,
    original_name   VARCHAR(255) NOT NULL,
    storage_key     TEXT NOT NULL,                      -- S3/local storage key
    file_size       BIGINT NOT NULL,
    mime_type       VARCHAR(100) NOT NULL,
    checksum        VARCHAR(64) NOT NULL,               -- SHA-256 for dedup
    status          document_status NOT NULL DEFAULT 'UPLOADED',
    extracted_data  JSONB,
    error_message   TEXT,
    fiscal_year     INTEGER,
    is_malware_clean BOOLEAN DEFAULT NULL,
    processed_by    VARCHAR(50),                        -- Which parser handled it
    uploaded_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed_at    TIMESTAMPTZ
);

CREATE INDEX idx_documents_msme ON documents(msme_id, document_type);
CREATE INDEX idx_documents_status ON documents(status);
CREATE UNIQUE INDEX idx_documents_checksum ON documents(msme_id, checksum);

-- =============================================================================
-- TABLE: digital_twins
-- =============================================================================
CREATE TABLE digital_twins (
    id                          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    msme_id                     UUID NOT NULL REFERENCES msmes(id) ON DELETE CASCADE,
    version                     INTEGER NOT NULL DEFAULT 1,
    
    -- Composite Scores (0-100)
    health_score                NUMERIC(6, 2) CHECK (health_score BETWEEN 0 AND 100),
    growth_trend_index          NUMERIC(6, 2),          -- Positive = growth, Negative = decline
    risk_index                  NUMERIC(6, 2) CHECK (risk_index BETWEEN 0 AND 100),
    liquidity_score             NUMERIC(6, 2) CHECK (liquidity_score BETWEEN 0 AND 100),
    profitability_score         NUMERIC(6, 2) CHECK (profitability_score BETWEEN 0 AND 100),
    solvency_score              NUMERIC(6, 2) CHECK (solvency_score BETWEEN 0 AND 100),
    compliance_score            NUMERIC(6, 2) CHECK (compliance_score BETWEEN 0 AND 100),
    
    -- Projections (JSONB for flexibility)
    cashflow_3m                 JSONB,                  -- {months: [...], values: [...]}
    cashflow_6m                 JSONB,
    cashflow_12m                JSONB,
    
    -- Benchmarks
    industry_benchmark          JSONB,                  -- {metric: {msme_val, industry_avg, percentile}}
    peer_group_id               VARCHAR(100),
    
    -- ML Features
    feature_vector              JSONB,                  -- 47 computed features
    qdrant_point_id             UUID,                   -- Reference to Qdrant vector
    
    -- Metadata
    narrative_summary           TEXT,                   -- LLM-generated text
    data_coverage_months        INTEGER,                -- How many months of data used
    confidence_level            VARCHAR(20),            -- HIGH, MEDIUM, LOW
    status                      twin_status NOT NULL DEFAULT 'GENERATING',
    generated_at                TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at                  TIMESTAMPTZ,
    generation_duration_ms      INTEGER,
    model_version               VARCHAR(50)
);

CREATE INDEX idx_twins_msme_version ON digital_twins(msme_id, version DESC);
CREATE INDEX idx_twins_msme_status ON digital_twins(msme_id, status);

COMMENT ON TABLE digital_twins IS 'AI-generated virtual representations of MSME financial state';

-- Now add FK to msmes table
ALTER TABLE msmes ADD CONSTRAINT fk_msmes_latest_twin
    FOREIGN KEY (latest_twin_id) REFERENCES digital_twins(id);

-- =============================================================================
-- TABLE: risk_predictions
-- =============================================================================
CREATE TABLE risk_predictions (
    id                          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    msme_id                     UUID NOT NULL REFERENCES msmes(id) ON DELETE CASCADE,
    twin_id                     UUID REFERENCES digital_twins(id),
    evaluation_id               UUID,                   -- FK added later
    
    -- Prediction Outputs
    risk_score                  NUMERIC(7, 2) NOT NULL CHECK (risk_score BETWEEN 0 AND 1000),
    probability_of_default      NUMERIC(5, 4) NOT NULL CHECK (probability_of_default BETWEEN 0 AND 1),
    recovery_probability        NUMERIC(5, 4) CHECK (recovery_probability BETWEEN 0 AND 1),
    confidence_score            NUMERIC(5, 4) CHECK (confidence_score BETWEEN 0 AND 1),
    risk_tier                   risk_tier NOT NULL,
    
    -- Individual Model Outputs
    lgbm_score                  NUMERIC(5, 4),
    xgb_score                   NUMERIC(5, 4),
    catboost_score              NUMERIC(5, 4),
    rf_score                    NUMERIC(5, 4),
    nn_score                    NUMERIC(5, 4),
    
    -- Explainability
    feature_importance          JSONB,                  -- [{feature, importance, direction}]
    shap_values                 JSONB,                  -- SHAP waterfall data
    lime_explanation            JSONB,                  -- LIME local explanation
    top_risk_factors            JSONB,                  -- [{factor, contribution, description}]
    
    -- Metadata
    model_version               VARCHAR(50) NOT NULL,
    features_used               INTEGER,
    predicted_at                TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_predictions_msme_date ON risk_predictions(msme_id, predicted_at DESC);
CREATE INDEX idx_predictions_tier ON risk_predictions(risk_tier, msme_id);

-- =============================================================================
-- TABLE: loan_evaluations
-- =============================================================================
CREATE TABLE loan_evaluations (
    id                          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    msme_id                     UUID NOT NULL REFERENCES msmes(id) ON DELETE CASCADE,
    twin_id                     UUID REFERENCES digital_twins(id),
    risk_prediction_id          UUID REFERENCES risk_predictions(id),
    agent_analysis_id           UUID,                   -- FK added later
    created_by                  UUID NOT NULL REFERENCES users(id),
    
    -- Loan Application Details
    loan_amount_requested       NUMERIC(15, 2) NOT NULL,
    loan_tenure_months          INTEGER NOT NULL,
    interest_rate               NUMERIC(5, 2),
    loan_purpose                VARCHAR(200) NOT NULL,
    loan_type                   VARCHAR(100),
    collateral_value            NUMERIC(15, 2) DEFAULT 0,
    collateral_type             VARCHAR(100),
    collateral_description      TEXT,
    
    -- AI Decision
    ai_recommendation           loan_recommendation,
    recommended_amount          NUMERIC(15, 2),
    recommended_tenure          INTEGER,
    ai_interest_rate            NUMERIC(5, 2),
    ai_confidence_score         NUMERIC(5, 4),
    ai_decision_summary         TEXT,
    emi_schedule                JSONB,                  -- Monthly EMI breakdown
    
    -- Final Decision
    final_decision              loan_recommendation,
    decided_by                  UUID REFERENCES users(id),
    decision_notes              TEXT,
    is_override                 BOOLEAN DEFAULT FALSE,
    override_reason_code        VARCHAR(50),
    override_reason_text        TEXT CHECK (is_override = FALSE OR LENGTH(override_reason_text) >= 100),
    
    -- Status
    status                      evaluation_status NOT NULL DEFAULT 'DRAFT',
    
    -- Timestamps
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at                TIMESTAMPTZ,
    decided_at                  TIMESTAMPTZ,
    locked_at                   TIMESTAMPTZ,            -- Locked after 7 days
    
    CONSTRAINT chk_loan_amount CHECK (loan_amount_requested > 0),
    CONSTRAINT chk_tenure CHECK (loan_tenure_months BETWEEN 1 AND 300)
);

CREATE INDEX idx_evaluations_msme ON loan_evaluations(msme_id, created_at DESC);
CREATE INDEX idx_evaluations_officer ON loan_evaluations(created_by, created_at DESC);
CREATE INDEX idx_evaluations_status ON loan_evaluations(status);

-- Add FK back to risk_predictions
ALTER TABLE risk_predictions ADD CONSTRAINT fk_predictions_evaluation
    FOREIGN KEY (evaluation_id) REFERENCES loan_evaluations(id);

-- =============================================================================
-- TABLE: agent_analyses
-- =============================================================================
CREATE TABLE agent_analyses (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    evaluation_id           UUID NOT NULL REFERENCES loan_evaluations(id) ON DELETE CASCADE,
    run_id                  VARCHAR(100) UNIQUE NOT NULL,    -- LangGraph run ID
    
    -- Individual Agent Outputs (JSONB for rich output)
    risk_agent_output       JSONB,
    fraud_agent_output      JSONB,
    financial_agent_output  JSONB,
    market_agent_output     JSONB,
    compliance_agent_output JSONB,
    recommendation_output   JSONB,
    explainability_output   JSONB,
    coordinator_output      JSONB,
    
    -- Aggregate Scores
    fraud_score             NUMERIC(5, 4),
    fraud_flags             TEXT[],
    compliance_score        NUMERIC(5, 4),
    
    -- Pipeline State
    pipeline_status         agent_pipeline_status NOT NULL DEFAULT 'QUEUED',
    agents_completed        TEXT[],
    agents_failed           TEXT[],
    error_message           TEXT,
    
    -- Performance
    duration_seconds        INTEGER,
    token_usage             INTEGER,
    llm_model_used          VARCHAR(100),
    
    started_at              TIMESTAMPTZ,
    completed_at            TIMESTAMPTZ,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_agent_analysis_eval ON agent_analyses(evaluation_id);

-- Update FK in loan_evaluations
ALTER TABLE loan_evaluations ADD CONSTRAINT fk_evaluations_agent
    FOREIGN KEY (agent_analysis_id) REFERENCES agent_analyses(id);

-- =============================================================================
-- TABLE: scenario_simulations
-- =============================================================================
CREATE TABLE scenario_simulations (
    id                          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    msme_id                     UUID NOT NULL REFERENCES msmes(id) ON DELETE CASCADE,
    evaluation_id               UUID REFERENCES loan_evaluations(id),
    created_by                  UUID NOT NULL REFERENCES users(id),
    
    -- Scenario Configuration
    scenario_name               VARCHAR(200),
    scenario_type               scenario_type NOT NULL,
    severity_percent            NUMERIC(5, 2) NOT NULL CHECK (severity_percent BETWEEN 0 AND 100),
    duration_months             INTEGER NOT NULL CHECK (duration_months BETWEEN 1 AND 60),
    probability                 NUMERIC(5, 4) DEFAULT 1.0 CHECK (probability BETWEEN 0 AND 1),
    compound_scenarios          JSONB,                  -- For compound scenario types
    
    -- Baseline State
    baseline_risk_score         NUMERIC(7, 2),
    baseline_pd                 NUMERIC(5, 4),
    baseline_health_score       NUMERIC(6, 2),
    baseline_cashflow           JSONB,
    
    -- Stressed State
    stressed_risk_score         NUMERIC(7, 2),
    stressed_pd                 NUMERIC(5, 4),
    stressed_health_score       NUMERIC(6, 2),
    stressed_cashflow           JSONB,
    
    -- Results
    delta_risk_score            NUMERIC(7, 2),
    delta_pd                    NUMERIC(5, 4),
    stress_test_passed          BOOLEAN,
    cashflow_comparison         JSONB,                  -- Month-by-month comparison
    full_simulation_output      JSONB,                  -- Complete simulation data
    
    -- Metadata
    duration_ms                 INTEGER,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_simulations_msme ON scenario_simulations(msme_id, created_at DESC);
CREATE INDEX idx_simulations_eval ON scenario_simulations(evaluation_id);

-- =============================================================================
-- TABLE: ews_alerts
-- =============================================================================
CREATE TABLE ews_alerts (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    msme_id                 UUID NOT NULL REFERENCES msmes(id) ON DELETE CASCADE,
    tenant_id               UUID NOT NULL REFERENCES tenants(id),
    
    -- Alert Content
    alert_code              VARCHAR(50) NOT NULL,       -- GST_NON_FILING, REVENUE_DECLINE, etc.
    alert_type              VARCHAR(100) NOT NULL,
    severity                alert_severity NOT NULL,
    ews_score               NUMERIC(6, 2),
    title                   VARCHAR(300) NOT NULL,
    reason                  TEXT NOT NULL,
    trigger_data            JSONB,                      -- Raw data that triggered the alert
    recommended_action      TEXT,
    
    -- Forecast
    default_probability_30d NUMERIC(5, 4),
    default_probability_60d NUMERIC(5, 4),
    default_probability_90d NUMERIC(5, 4),
    
    -- Resolution
    is_acknowledged         BOOLEAN NOT NULL DEFAULT FALSE,
    acknowledged_by         UUID REFERENCES users(id),
    acknowledged_at         TIMESTAMPTZ,
    acknowledgement_note    TEXT,
    is_resolved             BOOLEAN NOT NULL DEFAULT FALSE,
    resolved_at             TIMESTAMPTZ,
    resolution_note         TEXT,
    
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ews_msme ON ews_alerts(msme_id, created_at DESC);
CREATE INDEX idx_ews_tenant ON ews_alerts(tenant_id, severity, is_resolved, created_at DESC);
CREATE INDEX idx_ews_severity ON ews_alerts(severity, is_acknowledged);

-- =============================================================================
-- TABLE: notifications
-- =============================================================================
CREATE TABLE notifications (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    type            notification_type NOT NULL,
    title           VARCHAR(300) NOT NULL,
    body            TEXT NOT NULL,
    action_url      TEXT,
    metadata        JSONB DEFAULT '{}',
    is_read         BOOLEAN NOT NULL DEFAULT FALSE,
    read_at         TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_notifications_user ON notifications(user_id, is_read, created_at DESC);
CREATE INDEX idx_notifications_tenant ON notifications(tenant_id, created_at DESC);

-- =============================================================================
-- TABLE: notification_preferences
-- =============================================================================
CREATE TABLE notification_preferences (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_type      notification_type NOT NULL,
    in_app          BOOLEAN NOT NULL DEFAULT TRUE,
    email           BOOLEAN NOT NULL DEFAULT TRUE,
    sms             BOOLEAN NOT NULL DEFAULT FALSE,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, event_type)
);

-- =============================================================================
-- TABLE: audit_logs
-- =============================================================================
CREATE TABLE audit_logs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    user_id         UUID REFERENCES users(id),
    entity_type     VARCHAR(100) NOT NULL,
    entity_id       UUID,
    action          VARCHAR(50) NOT NULL,               -- CREATE, UPDATE, DELETE, LOGIN, etc.
    old_values      JSONB,
    new_values      JSONB,
    diff            JSONB,                              -- Computed diff of old vs new
    ip_address      INET,
    user_agent      TEXT,
    request_id      UUID,
    description     TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
) PARTITION BY RANGE (created_at);

-- Create partitions by year for performance
CREATE TABLE audit_logs_2026 PARTITION OF audit_logs
    FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');
CREATE TABLE audit_logs_2027 PARTITION OF audit_logs
    FOR VALUES FROM ('2027-01-01') TO ('2028-01-01');
CREATE TABLE audit_logs_2028 PARTITION OF audit_logs
    FOR VALUES FROM ('2028-01-01') TO ('2029-01-01');

CREATE INDEX idx_audit_tenant ON audit_logs(tenant_id, created_at DESC);
CREATE INDEX idx_audit_user ON audit_logs(user_id, created_at DESC);
CREATE INDEX idx_audit_entity ON audit_logs(entity_type, entity_id, created_at DESC);

COMMENT ON TABLE audit_logs IS 'Immutable audit trail — partitioned by year for performance. 7-year retention per RBI.';

-- =============================================================================
-- TABLE: reports
-- =============================================================================
CREATE TABLE reports (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    requested_by    UUID NOT NULL REFERENCES users(id),
    report_type     report_type NOT NULL,
    format          report_format NOT NULL,
    title           VARCHAR(300),
    parameters      JSONB NOT NULL DEFAULT '{}',
    status          report_status NOT NULL DEFAULT 'PENDING',
    storage_key     TEXT,
    file_size       BIGINT,
    error_message   TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMPTZ,
    expires_at      TIMESTAMPTZ DEFAULT NOW() + INTERVAL '7 days'
);

CREATE INDEX idx_reports_user ON reports(requested_by, created_at DESC);

-- =============================================================================
-- TABLE: ews_monitoring_runs
-- =============================================================================
CREATE TABLE ews_monitoring_runs (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id           UUID NOT NULL REFERENCES tenants(id),
    msmes_evaluated     INTEGER NOT NULL DEFAULT 0,
    alerts_generated    INTEGER NOT NULL DEFAULT 0,
    critical_alerts     INTEGER NOT NULL DEFAULT 0,
    warning_alerts      INTEGER NOT NULL DEFAULT 0,
    duration_seconds    INTEGER,
    status              VARCHAR(20) NOT NULL DEFAULT 'RUNNING',
    error_message       TEXT,
    started_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at        TIMESTAMPTZ
);

-- =============================================================================
-- TABLE: industry_benchmarks
-- =============================================================================
CREATE TABLE industry_benchmarks (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    industry_type       VARCHAR(100) NOT NULL,
    sub_industry        VARCHAR(100),
    state               VARCHAR(100),
    metric_name         VARCHAR(100) NOT NULL,
    median_value        NUMERIC(12, 4),
    p25_value           NUMERIC(12, 4),
    p75_value           NUMERIC(12, 4),
    data_year           INTEGER NOT NULL,
    sample_size         INTEGER,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(industry_type, sub_industry, state, metric_name, data_year)
);

CREATE INDEX idx_benchmarks_industry ON industry_benchmarks(industry_type, data_year DESC);

-- =============================================================================
-- TABLE: system_settings
-- =============================================================================
CREATE TABLE system_settings (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id   UUID REFERENCES tenants(id),            -- NULL = global settings
    key         VARCHAR(100) NOT NULL,
    value       JSONB NOT NULL,
    description TEXT,
    updated_by  UUID REFERENCES users(id),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(tenant_id, key)
);

-- =============================================================================
-- TABLE: model_registry
-- =============================================================================
CREATE TABLE model_registry (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_name      VARCHAR(100) NOT NULL,
    version         VARCHAR(50) NOT NULL,
    model_type      VARCHAR(50) NOT NULL,               -- LIGHTGBM, XGBOOST, etc.
    storage_path    TEXT NOT NULL,
    metrics         JSONB NOT NULL DEFAULT '{}',        -- AUC, F1, precision, recall
    feature_schema  JSONB,                              -- Expected input features
    is_active       BOOLEAN NOT NULL DEFAULT FALSE,
    trained_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deployed_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(model_name, version)
);

-- =============================================================================
-- VIEWS
-- =============================================================================

-- View: MSME Portfolio Summary
CREATE OR REPLACE VIEW v_portfolio_summary AS
SELECT
    m.tenant_id,
    COUNT(DISTINCT m.id)                                          AS total_msmes,
    COUNT(DISTINCT le.id)                                         AS total_evaluations,
    SUM(le.loan_amount_requested)                                 AS total_portfolio_value,
    SUM(CASE WHEN le.final_decision = 'APPROVE' THEN le.recommended_amount ELSE 0 END) AS total_approved_value,
    AVG(rp.risk_score)                                            AS avg_risk_score,
    COUNT(CASE WHEN m.risk_tier IN ('HIGH', 'VERY_HIGH') THEN 1 END) AS high_risk_count,
    COUNT(CASE WHEN ea.is_resolved = FALSE AND ea.severity = 'CRITICAL' THEN 1 END) AS critical_alerts,
    COUNT(CASE WHEN ea.is_resolved = FALSE THEN 1 END)            AS open_alerts,
    AVG(rp.probability_of_default) * 100                          AS avg_pd_percent
FROM msmes m
LEFT JOIN loan_evaluations le ON le.msme_id = m.id AND le.status = 'COMPLETED'
LEFT JOIN risk_predictions rp ON rp.id = le.risk_prediction_id
LEFT JOIN ews_alerts ea ON ea.msme_id = m.id
WHERE m.deleted_at IS NULL
GROUP BY m.tenant_id;

-- View: MSME Risk Dashboard (latest state per MSME)
CREATE OR REPLACE VIEW v_msme_risk_dashboard AS
SELECT
    m.id,
    m.tenant_id,
    m.business_name,
    m.gstin,
    m.industry_type,
    m.state,
    m.district,
    m.status,
    m.risk_tier,
    m.data_completeness,
    m.assigned_officer,
    dt.health_score,
    dt.growth_trend_index,
    dt.risk_index,
    dt.generated_at     AS twin_generated_at,
    rp.risk_score       AS latest_risk_score,
    rp.probability_of_default,
    rp.confidence_score,
    rp.predicted_at     AS last_predicted_at,
    m.latest_ews_score,
    le.loan_amount_requested AS latest_loan_amount,
    le.ai_recommendation AS latest_ai_recommendation,
    m.created_at
FROM msmes m
LEFT JOIN digital_twins dt ON dt.id = m.latest_twin_id
LEFT JOIN LATERAL (
    SELECT * FROM risk_predictions
    WHERE msme_id = m.id
    ORDER BY predicted_at DESC LIMIT 1
) rp ON TRUE
LEFT JOIN LATERAL (
    SELECT * FROM loan_evaluations
    WHERE msme_id = m.id AND status = 'COMPLETED'
    ORDER BY created_at DESC LIMIT 1
) le ON TRUE
WHERE m.deleted_at IS NULL;

-- View: EWS Alert Summary by Tenant
CREATE OR REPLACE VIEW v_ews_summary AS
SELECT
    ea.tenant_id,
    COUNT(*)                                            AS total_alerts,
    COUNT(CASE WHEN ea.severity = 'CRITICAL' THEN 1 END) AS critical_count,
    COUNT(CASE WHEN ea.severity = 'WARNING' THEN 1 END)  AS warning_count,
    COUNT(CASE WHEN ea.severity = 'INFO' THEN 1 END)     AS info_count,
    COUNT(CASE WHEN ea.is_acknowledged = FALSE THEN 1 END) AS unacknowledged_count,
    COUNT(CASE WHEN ea.is_resolved = FALSE THEN 1 END)   AS open_count,
    MAX(ea.created_at)                                  AS latest_alert_at
FROM ews_alerts ea
WHERE ea.created_at >= NOW() - INTERVAL '30 days'
GROUP BY ea.tenant_id;

-- View: Industry Risk Distribution
CREATE OR REPLACE VIEW v_industry_risk_distribution AS
SELECT
    m.tenant_id,
    m.industry_type,
    COUNT(*)                                                        AS msme_count,
    AVG(rp.risk_score)                                             AS avg_risk_score,
    AVG(rp.probability_of_default)                                 AS avg_pd,
    COUNT(CASE WHEN m.risk_tier = 'VERY_HIGH' THEN 1 END)          AS very_high_risk,
    COUNT(CASE WHEN m.risk_tier = 'HIGH' THEN 1 END)               AS high_risk,
    COUNT(CASE WHEN m.risk_tier = 'MEDIUM' THEN 1 END)             AS medium_risk,
    COUNT(CASE WHEN m.risk_tier IN ('LOW', 'VERY_LOW') THEN 1 END) AS low_risk
FROM msmes m
LEFT JOIN LATERAL (
    SELECT risk_score, probability_of_default
    FROM risk_predictions
    WHERE msme_id = m.id
    ORDER BY predicted_at DESC LIMIT 1
) rp ON TRUE
WHERE m.deleted_at IS NULL
GROUP BY m.tenant_id, m.industry_type;

-- View: State-wise Risk Heatmap Data
CREATE OR REPLACE VIEW v_state_risk_heatmap AS
SELECT
    m.tenant_id,
    m.state,
    m.district,
    COUNT(DISTINCT m.id)            AS msme_count,
    AVG(rp.risk_score)             AS avg_risk_score,
    AVG(rp.probability_of_default) AS avg_pd,
    COUNT(CASE WHEN m.risk_tier IN ('HIGH', 'VERY_HIGH') THEN 1 END) AS high_risk_count,
    SUM(le.loan_amount_requested)  AS total_exposure
FROM msmes m
LEFT JOIN LATERAL (
    SELECT risk_score, probability_of_default
    FROM risk_predictions
    WHERE msme_id = m.id
    ORDER BY predicted_at DESC LIMIT 1
) rp ON TRUE
LEFT JOIN LATERAL (
    SELECT loan_amount_requested
    FROM loan_evaluations
    WHERE msme_id = m.id AND status = 'COMPLETED'
    ORDER BY created_at DESC LIMIT 1
) le ON TRUE
WHERE m.deleted_at IS NULL
GROUP BY m.tenant_id, m.state, m.district;

-- =============================================================================
-- TRIGGERS
-- =============================================================================

-- Trigger function: auto-update updated_at
CREATE OR REPLACE FUNCTION fn_update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at trigger to all relevant tables
CREATE TRIGGER trg_tenants_updated_at
    BEFORE UPDATE ON tenants
    FOR EACH ROW EXECUTE FUNCTION fn_update_updated_at();

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION fn_update_updated_at();

CREATE TRIGGER trg_msmes_updated_at
    BEFORE UPDATE ON msmes
    FOR EACH ROW EXECUTE FUNCTION fn_update_updated_at();

CREATE TRIGGER trg_financial_data_updated_at
    BEFORE UPDATE ON financial_data
    FOR EACH ROW EXECUTE FUNCTION fn_update_updated_at();

-- Trigger function: auto-compute financial ratios
CREATE OR REPLACE FUNCTION fn_compute_financial_ratios()
RETURNS TRIGGER AS $$
BEGIN
    -- Current Ratio
    IF NEW.current_liabilities IS NOT NULL AND NEW.current_liabilities > 0 THEN
        NEW.current_ratio := NEW.current_assets / NEW.current_liabilities;
    END IF;
    
    -- Quick Ratio
    IF NEW.current_liabilities IS NOT NULL AND NEW.current_liabilities > 0 THEN
        NEW.quick_ratio := (COALESCE(NEW.current_assets, 0) - COALESCE(NEW.inventory, 0)) / NEW.current_liabilities;
    END IF;
    
    -- Debt to Equity
    IF NEW.equity IS NOT NULL AND NEW.equity > 0 THEN
        NEW.debt_to_equity := COALESCE(NEW.debt, 0) / NEW.equity;
    END IF;
    
    -- Interest Coverage
    IF NEW.interest_expense IS NOT NULL AND NEW.interest_expense > 0 THEN
        NEW.interest_coverage := COALESCE(NEW.ebit, 0) / NEW.interest_expense;
    END IF;
    
    -- Return on Assets
    IF NEW.total_assets IS NOT NULL AND NEW.total_assets > 0 THEN
        NEW.return_on_assets := COALESCE(NEW.net_profit, 0) / NEW.total_assets;
    END IF;
    
    -- Return on Equity
    IF NEW.equity IS NOT NULL AND NEW.equity > 0 THEN
        NEW.return_on_equity := COALESCE(NEW.net_profit, 0) / NEW.equity;
    END IF;
    
    -- Net Profit Margin
    IF NEW.revenue IS NOT NULL AND NEW.revenue > 0 THEN
        NEW.net_profit_margin := COALESCE(NEW.net_profit, 0) / NEW.revenue;
        NEW.asset_turnover := NEW.revenue / COALESCE(NULLIF(NEW.total_assets, 0), 1);
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_compute_financial_ratios
    BEFORE INSERT OR UPDATE ON financial_data
    FOR EACH ROW EXECUTE FUNCTION fn_compute_financial_ratios();

-- Trigger function: update MSME risk tier when risk prediction is inserted
CREATE OR REPLACE FUNCTION fn_update_msme_risk_tier()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE msmes
    SET risk_tier = NEW.risk_tier,
        latest_risk_score = NEW.risk_score,
        updated_at = NOW()
    WHERE id = NEW.msme_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_msme_risk_tier
    AFTER INSERT ON risk_predictions
    FOR EACH ROW EXECUTE FUNCTION fn_update_msme_risk_tier();

-- Trigger function: update MSME latest_twin_id when twin is completed
CREATE OR REPLACE FUNCTION fn_update_msme_latest_twin()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'ACTIVE' THEN
        UPDATE msmes
        SET latest_twin_id = NEW.id,
            updated_at = NOW()
        WHERE id = NEW.msme_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_msme_latest_twin
    AFTER INSERT OR UPDATE ON digital_twins
    FOR EACH ROW EXECUTE FUNCTION fn_update_msme_latest_twin();

-- Trigger: Lock evaluation after 7 days
CREATE OR REPLACE FUNCTION fn_lock_completed_evaluation()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'COMPLETED' AND OLD.status != 'COMPLETED' THEN
        NEW.locked_at = NOW() + INTERVAL '7 days';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_lock_evaluation
    BEFORE UPDATE ON loan_evaluations
    FOR EACH ROW EXECUTE FUNCTION fn_lock_completed_evaluation();

-- =============================================================================
-- STORED PROCEDURES
-- =============================================================================

-- Procedure: Get MSME data completeness score
CREATE OR REPLACE FUNCTION fn_compute_data_completeness(p_msme_id UUID)
RETURNS INTEGER AS $$
DECLARE
    v_score INTEGER := 0;
    v_has_financials BOOLEAN;
    v_has_gst BOOLEAN;
    v_has_credit BOOLEAN;
    v_has_transactions BOOLEAN;
    v_fiscal_years INTEGER;
BEGIN
    -- Check financial data (40 points, +10 per year up to 4)
    SELECT 
        COUNT(DISTINCT fiscal_year) > 0,
        LEAST(COUNT(DISTINCT fiscal_year), 4) * 10
    INTO v_has_financials, v_fiscal_years
    FROM financial_data
    WHERE msme_id = p_msme_id;
    
    IF v_has_financials THEN
        v_score := v_score + v_fiscal_years;
    END IF;
    
    -- Check GST data (20 points)
    SELECT COUNT(*) > 0
    INTO v_has_gst
    FROM gst_data
    WHERE msme_id = p_msme_id;
    
    IF v_has_gst THEN v_score := v_score + 20; END IF;
    
    -- Check credit data (20 points)
    SELECT COUNT(*) > 0
    INTO v_has_credit
    FROM credit_data
    WHERE msme_id = p_msme_id;
    
    IF v_has_credit THEN v_score := v_score + 20; END IF;
    
    -- Check transactions (20 points)
    SELECT COUNT(*) > 0
    INTO v_has_transactions
    FROM bank_transactions
    WHERE msme_id = p_msme_id;
    
    IF v_has_transactions THEN v_score := v_score + 20; END IF;
    
    -- Update the MSME record
    UPDATE msmes SET data_completeness = v_score, updated_at = NOW()
    WHERE id = p_msme_id;
    
    RETURN v_score;
END;
$$ LANGUAGE plpgsql;

-- Procedure: Get portfolio statistics for a tenant
CREATE OR REPLACE FUNCTION fn_portfolio_stats(p_tenant_id UUID)
RETURNS TABLE (
    total_msmes         BIGINT,
    active_msmes        BIGINT,
    total_loan_value    NUMERIC,
    approved_value      NUMERIC,
    avg_risk_score      NUMERIC,
    npa_count           BIGINT,
    critical_alerts     BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(DISTINCT m.id)::BIGINT,
        COUNT(DISTINCT CASE WHEN m.status = 'ACTIVE' THEN m.id END)::BIGINT,
        COALESCE(SUM(le.loan_amount_requested), 0),
        COALESCE(SUM(CASE WHEN le.final_decision = 'APPROVE' THEN le.recommended_amount ELSE 0 END), 0),
        COALESCE(AVG(rp.risk_score), 0),
        COUNT(DISTINCT CASE WHEN rp.risk_tier = 'VERY_HIGH' THEN m.id END)::BIGINT,
        COUNT(DISTINCT CASE WHEN ea.severity = 'CRITICAL' AND ea.is_resolved = FALSE THEN ea.id END)::BIGINT
    FROM msmes m
    LEFT JOIN loan_evaluations le ON le.msme_id = m.id AND le.status = 'COMPLETED'
    LEFT JOIN risk_predictions rp ON rp.id = le.risk_prediction_id
    LEFT JOIN ews_alerts ea ON ea.msme_id = m.id
    WHERE m.tenant_id = p_tenant_id AND m.deleted_at IS NULL;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- SEED DATA
-- =============================================================================

-- Default tenant
INSERT INTO tenants (id, name, code, settings) VALUES
    ('00000000-0000-0000-0000-000000000001', 'IDBI Bank', 'IDBI', '{"default_risk_thresholds": {"high": 650, "critical": 800}}'),
    ('00000000-0000-0000-0000-000000000002', 'Demo Bank', 'DEMO', '{}');

-- Default admin user (password: Admin@123!)
INSERT INTO users (id, tenant_id, email, password_hash, first_name, last_name, role) VALUES
    ('00000000-0000-0000-0001-000000000001',
     '00000000-0000-0000-0000-000000000001',
     'admin@idbi.fintwin.ai',
     '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TsGiUWCHe0tXMqZ5a5X5X5X5X5X5',
     'System', 'Admin', 'BANK_ADMIN'),
    ('00000000-0000-0000-0001-000000000002',
     '00000000-0000-0000-0000-000000000001',
     'riskmanager@idbi.fintwin.ai',
     '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TsGiUWCHe0tXMqZ5a5X5X5X5X5X5',
     'Risk', 'Manager', 'RISK_MANAGER');

-- Industry benchmarks (sample)
INSERT INTO industry_benchmarks (industry_type, metric_name, median_value, p25_value, p75_value, data_year) VALUES
    ('Manufacturing', 'current_ratio', 1.5, 1.1, 2.1, 2025),
    ('Manufacturing', 'debt_to_equity', 1.2, 0.7, 2.0, 2025),
    ('Manufacturing', 'net_profit_margin', 0.07, 0.03, 0.12, 2025),
    ('Retail Trade', 'current_ratio', 1.3, 0.9, 1.8, 2025),
    ('Retail Trade', 'net_profit_margin', 0.04, 0.02, 0.08, 2025),
    ('IT Services', 'current_ratio', 2.1, 1.5, 3.0, 2025),
    ('IT Services', 'net_profit_margin', 0.15, 0.08, 0.25, 2025),
    ('Food Processing', 'current_ratio', 1.4, 1.0, 1.9, 2025),
    ('Textile', 'current_ratio', 1.2, 0.8, 1.7, 2025),
    ('Construction', 'debt_to_equity', 1.8, 1.0, 2.8, 2025);

-- System settings
INSERT INTO system_settings (tenant_id, key, value, description) VALUES
    (NULL, 'ews.gst_nonfile_warning_months', '2', 'GST non-filing months to trigger WARNING alert'),
    (NULL, 'ews.gst_nonfile_critical_months', '3', 'GST non-filing months to trigger CRITICAL alert'),
    (NULL, 'ews.revenue_decline_warning_pct', '20', 'Revenue decline % to trigger WARNING'),
    (NULL, 'ews.revenue_decline_critical_pct', '40', 'Revenue decline % to trigger CRITICAL'),
    (NULL, 'ews.credit_score_drop_warning', '50', 'Credit score drop points for WARNING'),
    (NULL, 'ews.credit_score_drop_critical', '100', 'Credit score drop points for CRITICAL'),
    (NULL, 'risk.pd_senior_review_threshold', '0.40', 'PD above which senior review is required'),
    (NULL, 'risk.fraud_auto_reject_threshold', '0.90', 'Fraud score above which auto-reject triggers'),
    (NULL, 'digital_twin.expiry_days', '30', 'Days after which twin is marked stale'),
    (NULL, 'loan.max_officer_approval_amount', '5000000', 'Max loan amount Loan Officer can approve (50L)');

-- =============================================================================
-- GRANT PERMISSIONS (application user)
-- =============================================================================

-- Create application user (run as superuser, adjust password)
-- CREATE USER fintwin_app WITH PASSWORD 'CHANGE_ME_IN_ENV';
-- GRANT CONNECT ON DATABASE fintwin_db TO fintwin_app;
-- GRANT USAGE ON SCHEMA public TO fintwin_app;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO fintwin_app;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO fintwin_app;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO fintwin_app;

-- =============================================================================
-- END OF SCHEMA
-- =============================================================================
