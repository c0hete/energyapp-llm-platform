-- Migration: Add audit_logs table
-- Description: Centralized audit logging system for tracking all user actions
-- Date: 2025-12-11

CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGSERIAL PRIMARY KEY,

    -- Who performed the action
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    user_email VARCHAR(255),  -- Denormalized for fast queries
    user_role VARCHAR(50),    -- Denormalized for fast queries

    -- What was done
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id INTEGER,

    -- Context
    metadata TEXT,  -- JSON string for flexible data storage

    -- Result
    status VARCHAR(20) NOT NULL DEFAULT 'success',  -- success, failed, blocked
    error_message TEXT,

    -- When and where
    ip_address VARCHAR(45),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_status ON audit_logs(status);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_logs_resource_type ON audit_logs(resource_type);

-- Composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_audit_user_time ON audit_logs(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_audit_action_time ON audit_logs(action, created_at);
CREATE INDEX IF NOT EXISTS idx_audit_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_audit_status_time ON audit_logs(status, created_at);

-- Add comment for documentation
COMMENT ON TABLE audit_logs IS 'Centralized audit logging for all system activities';
COMMENT ON COLUMN audit_logs.metadata IS 'JSON string containing additional contextual information';
COMMENT ON COLUMN audit_logs.user_email IS 'Denormalized for performance - allows querying without JOIN';
COMMENT ON COLUMN audit_logs.user_role IS 'Denormalized for performance - captures role at time of action';
