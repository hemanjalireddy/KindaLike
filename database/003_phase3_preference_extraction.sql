-- ============================================
-- 0. PRE-REQUISITES (Functions & Users)
-- ============================================

-- Ensure the update timestamp function exists
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- (Assuming 'users' table already exists from Auth module. 
-- If not, uncomment the lines below to create a minimal one)
-- CREATE TABLE IF NOT EXISTS users (
--     id SERIAL PRIMARY KEY,
--     email VARCHAR(255) UNIQUE NOT NULL,
--     password_hash VARCHAR(255) NOT NULL,
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );

-- ============================================
-- 1. CHATBOT TABLES (Required for Chatbot.py)
-- ============================================
DROP TABLE IF EXISTS chat_messages CASCADE;
DROP TABLE IF EXISTS chat_sessions CASCADE;

CREATE TABLE chat_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE chat_messages (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL, -- 'user' or 'assistant'
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 2. PHASE 3 PREFERENCE TABLES (Your Code)
-- ============================================

-- A. Restaurants (Cache)
CREATE TABLE IF NOT EXISTS restaurants (
    id SERIAL PRIMARY KEY,
    yelp_id VARCHAR(100) UNIQUE,
    google_place_id VARCHAR(100) UNIQUE,
    name VARCHAR(255) NOT NULL,
    address VARCHAR(500),
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(20),
    country VARCHAR(50) DEFAULT 'US',
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    phone VARCHAR(20),
    price_level INTEGER CHECK (price_level BETWEEN 1 AND 4),
    rating DECIMAL(2, 1),
    review_count INTEGER DEFAULT 0,
    categories JSONB,
    yelp_url VARCHAR(500),
    google_url VARCHAR(500),
    website_url VARCHAR(500),
    image_url VARCHAR(500),
    yelp_data JSONB,
    google_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_api_fetch TIMESTAMP
);

-- B. User Initial Selections (Onboarding)
DROP TABLE IF EXISTS user_initial_restaurants CASCADE;
CREATE TABLE user_initial_restaurants (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    restaurant_id INTEGER REFERENCES restaurants(id) ON DELETE CASCADE,
    selection_order INTEGER CHECK (selection_order BETWEEN 1 AND 3),
    user_notes TEXT,
    favorite_dish VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_user_restaurant UNIQUE(user_id, restaurant_id)
);

-- C. User Preferences (The Core Engine)
DROP TABLE IF EXISTS user_preferences CASCADE;
CREATE TABLE user_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    category VARCHAR(50) NOT NULL,
    subcategory VARCHAR(50),
    value_text VARCHAR(255),
    value_numeric DECIMAL(10, 2),
    value_json JSONB,
    confidence_score DECIMAL(3, 2) DEFAULT 0.50,
    weight DECIMAL(3, 2) DEFAULT 0.10,
    source VARCHAR(50) DEFAULT 'onboarding',
    derived_from_restaurants INTEGER[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_user_preference UNIQUE(user_id, category, subcategory)
);

-- D. Analysis Logs (Debugging & History)
DROP TABLE IF EXISTS preference_analyses CASCADE;
CREATE TABLE preference_analyses (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    restaurant_ids INTEGER[] NOT NULL,
    yelp_data JSONB,
    google_data JSONB,
    llm_insights JSONB,
    user_questionnaire_responses JSONB,
    preference_summary JSONB,
    processing_status VARCHAR(20) DEFAULT 'pending',
    processing_version VARCHAR(20) DEFAULT '1.0',
    processing_duration_ms INTEGER,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    CONSTRAINT one_analysis_per_user UNIQUE(user_id)
);

-- E. Questionnaire Responses
DROP TABLE IF EXISTS user_questionnaire_responses CASCADE;
CREATE TABLE user_questionnaire_responses (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    restaurant_id INTEGER REFERENCES restaurants(id),
    question_id VARCHAR(50) NOT NULL,
    question_text TEXT NOT NULL,
    answer_value JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_user_question UNIQUE(user_id, question_id)
);

-- ============================================
-- 3. TRIGGERS
-- ============================================
DROP TRIGGER IF EXISTS update_restaurants_updated_at ON restaurants;
CREATE TRIGGER update_restaurants_updated_at
    BEFORE UPDATE ON restaurants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_user_preferences_updated_at ON user_preferences;
CREATE TRIGGER update_user_preferences_updated_at
    BEFORE UPDATE ON user_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_chat_sessions_updated_at ON chat_sessions;
CREATE TRIGGER update_chat_sessions_updated_at
    BEFORE UPDATE ON chat_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 4. DUMMY DATA (To prevent empty UI crashes)
-- ============================================
-- Ensure we have a user (ID 1)
INSERT INTO users (username, password_hash)
VALUES ('testuser', 'hashedpassword')
ON CONFLICT DO NOTHING;

-- Insert basic preferences for User 1
INSERT INTO user_preferences (user_id, category, subcategory, value_text, confidence_score)
VALUES 
(1, 'cuisine', NULL, 'Thai', 0.9),
(1, 'price', NULL, '$$', 0.8),
(1, 'ambiance', NULL, 'Casual', 0.7)
ON CONFLICT DO NOTHING;