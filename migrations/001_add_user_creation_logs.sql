-- Add user_creation_logs table for audit trail
CREATE TABLE IF NOT EXISTS user_creation_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_by_admin_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    reason TEXT,
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_ucl_user_id ON user_creation_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_ucl_created_at ON user_creation_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_ucl_admin_id ON user_creation_logs(created_by_admin_id);

-- Add comment
COMMENT ON TABLE user_creation_logs IS 'Registro de auditoría de creación de usuarios';
COMMENT ON COLUMN user_creation_logs.reason IS 'Motivo por el cual se creó el usuario';
COMMENT ON COLUMN user_creation_logs.created_by_admin_id IS 'ID del admin que creó al usuario (NULL si fue auto-registro)';
