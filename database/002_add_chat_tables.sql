-- Migration: Add chat tables for restaurant recommendation chatbot

-- Create chat_sessions table
CREATE TABLE IF NOT EXISTS chat_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_message_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Create chat_messages table
CREATE TABLE IF NOT EXISTS chat_messages (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    recommendations JSONB, -- Store restaurant recommendations as JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index on session_id for faster message retrieval
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id);

-- Create index on user_id for faster session lookups
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id);

-- Create index on active sessions
CREATE INDEX IF NOT EXISTS idx_chat_sessions_active ON chat_sessions(is_active);

-- Function to update last_message_at timestamp
CREATE OR REPLACE FUNCTION update_session_last_message()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE chat_sessions
    SET last_message_at = CURRENT_TIMESTAMP
    WHERE id = NEW.session_id;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to automatically update last_message_at
CREATE TRIGGER update_session_timestamp
    AFTER INSERT ON chat_messages
    FOR EACH ROW
    EXECUTE FUNCTION update_session_last_message();

-- Comments for documentation
COMMENT ON TABLE chat_sessions IS 'Stores chat sessions for restaurant recommendations';
COMMENT ON TABLE chat_messages IS 'Stores individual messages in chat sessions';
COMMENT ON COLUMN chat_messages.recommendations IS 'JSON array of restaurant recommendations with details';
