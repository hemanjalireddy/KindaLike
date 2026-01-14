# Chatbot Setup Guide

This guide explains how to set up and use the AI-powered restaurant recommendation chatbot.

## Features

The chatbot provides:
- **LLM-Powered Understanding**: Uses GPT-4o to understand natural language requests
- **Yelp Integration**: Searches real restaurants using Yelp Fusion API
- **User Preferences**: Considers your saved preferences from the survey
- **IP Geolocation**: Automatically detects your location (or you can override it)
- **Conversation History**: Stores chat sessions and messages in PostgreSQL

## Architecture

```
User Query → LLM Service → Category Generation → Yelp API → Restaurant Results
                ↓                                               ↓
           User Preferences                            Database Storage
                ↓                                               ↓
          Location Service                           Chat History
```

## Required API Keys

You need two API keys to use the chatbot:

### 1. Yelp API Key

**Get your key:**
1. Go to https://www.yelp.com/developers
2. Create a Yelp account (if you don't have one)
3. Create a new app
4. Copy your API key

**Add to .env:**
```env
YELP_API_KEY=your_actual_yelp_api_key_here
```

### 2. LiteLLM API Key (GPT-4o Access)

Since you're using Cornell's LiteLLM endpoint, you need your Cornell API key.

**Add to .env:**
```env
LITELLM_API_KEY=your_cornell_api_key_here
LITELLM_BASE_URL=https://api.ai.it.cornell.edu
LITELLM_MODEL=openai.gpt-4o
```

## Setup Instructions

### Step 1: Add API Keys

1. Open `backend/.env` file
2. Replace the placeholder values:
   ```env
   YELP_API_KEY=your_actual_yelp_api_key_here
   LITELLM_API_KEY=your_actual_cornell_api_key_here
   ```

### Step 2: Rebuild Backend Container

Since we added new dependencies, rebuild the backend:

```bash
# Stop all containers
docker-compose down

# Rebuild backend with new dependencies
docker-compose up -d --build backend

# Or rebuild everything
docker-compose up -d --build
```

### Step 3: Verify Services

Check that all services are running:

```bash
docker-compose ps
```

You should see:
- ✅ `kindalike_frontend` (running)
- ✅ `kindalike_backend` (running)
- ✅ `kindalike_db` (running)

### Step 4: Test the Chatbot

1. Open http://localhost in your browser
2. Login or create an account
3. Complete the preferences survey
4. You'll be redirected to the chatbot
5. Try asking: "I want Italian food for a romantic date night"

## How It Works

### 1. User Flow

```
Login → Survey → Chatbot → Get Recommendations
```

After completing the survey, users are automatically directed to the chatbot interface.

### 2. Chatbot Request Flow

When you send a message:

1. **Authentication**: Verifies your JWT token
2. **Session Management**: Creates or uses existing chat session
3. **Location Detection**: Gets your location from IP (or uses manual override)
4. **User Preferences**: Fetches your saved preferences from database
5. **LLM Processing**: GPT-4o analyzes your request and generates search categories
6. **Yelp Search**: Searches Yelp API with generated parameters
7. **Response**: Returns top 5 restaurant recommendations
8. **Storage**: Saves conversation to database

### 3. LLM Category Generation

The LLM analyzes your query and generates:

```json
{
  "hierarchical_categories": ["Food & Dining", "Restaurants", "Italian"],
  "primary_categories": ["italian", "restaurants"],
  "attributes": {
    "cuisine_type": "Italian",
    "price_level": 3,
    "occasion": "date night",
    "ambiance_keywords": ["romantic", "intimate"],
    "special_features": ["reservations", "outdoor seating"]
  },
  "reasoning": "User wants Italian food in an upscale, romantic setting"
}
```

### 4. Yelp API Search

The Yelp service uses these parameters to search:

- **Location**: Auto-detected or user-provided
- **Categories**: From LLM output
- **Price**: From LLM or user preferences
- **Term**: Cuisine + ambiance keywords
- **Attributes**: Special features (reservations, outdoor seating, etc.)

### 5. Database Storage

Chat history is stored in two tables:

**`chat_sessions`**:
- User's chat sessions
- Start time, last message time
- Active/inactive status

**`chat_messages`**:
- Individual messages (user and assistant)
- Restaurant recommendations (stored as JSONB)
- Timestamps

## API Endpoints

The chatbot uses these endpoints:

### Send Message
```
POST /api/chat/message
Authorization: Bearer <token>
Body: {
  "message": "I want Italian food",
  "session_id": 1,  // optional
  "location": "Ithaca, NY"  // optional
}

Response: {
  "session_id": 1,
  "message_id": 5,
  "response": "Based on your request...",
  "recommendations": [...]
}
```

### Get Chat Sessions
```
GET /api/chat/sessions
Authorization: Bearer <token>

Response: [
  {
    "id": 1,
    "started_at": "2024-01-15T10:30:00",
    "last_message_at": "2024-01-15T10:45:00",
    "is_active": true,
    "message_count": 10
  }
]
```

### Get Session Messages
```
GET /api/chat/sessions/{session_id}/messages
Authorization: Bearer <token>

Response: [
  {
    "id": 1,
    "role": "user",
    "content": "I want Italian food",
    "recommendations": null,
    "created_at": "2024-01-15T10:30:00"
  },
  {
    "id": 2,
    "role": "assistant",
    "content": "Here are my recommendations...",
    "recommendations": [...],
    "created_at": "2024-01-15T10:30:05"
  }
]
```

### Create New Session
```
POST /api/chat/sessions/new
Authorization: Bearer <token>

Response: {
  "id": 2,
  "started_at": "2024-01-15T11:00:00",
  "last_message_at": "2024-01-15T11:00:00",
  "is_active": true,
  "message_count": 0
}
```

## Code Structure

### Backend Services

**`backend/app/services/llm_service.py`**
- LLM category generation using LangChain + GPT-4o
- System prompts for restaurant understanding
- Fallback logic if LLM fails

**`backend/app/services/yelp_service.py`**
- Yelp API integration
- Restaurant search with filters
- Result formatting for display

**`backend/app/services/location_service.py`**
- IP-based geolocation (ip-api.com)
- Automatic location detection
- City/region formatting

**`backend/app/routes/chatbot.py`**
- API endpoints for chat
- Request/response handling
- Database operations

### Frontend Components

**`src/pages/Chatbot.jsx`**
- Chat interface
- Message display (user/assistant)
- Restaurant recommendation cards
- Loading states and error handling

**`src/styles/Chatbot.css`**
- Modern chat UI styling
- Responsive design
- Animations and transitions

**`src/services/api.js`**
- Chat API functions
- Authentication handling

## Usage Examples

### Example Queries

Try these queries with the chatbot:

1. **Specific Cuisine**:
   - "I want Italian food for dinner"
   - "Find me a Japanese restaurant"

2. **Occasion-Based**:
   - "Where should I take my date tonight?"
   - "I need a place for a birthday celebration"
   - "Quick lunch spot near me"

3. **Dietary Requirements**:
   - "Vegetarian restaurants with outdoor seating"
   - "Vegan-friendly brunch spots"

4. **Ambiance**:
   - "Romantic restaurant with dim lighting"
   - "Family-friendly place with a casual vibe"
   - "Trendy spot for young professionals"

5. **Features**:
   - "Restaurants that take reservations"
   - "Places with live music"
   - "Outdoor dining options"

## Troubleshooting

### Backend Not Starting

If the backend fails to start after adding dependencies:

```bash
# Check logs
docker-compose logs backend

# Common issue: Missing dependencies
docker-compose down
docker-compose build --no-cache backend
docker-compose up -d
```

### LLM API Errors

If you see LLM-related errors:

1. Check API key is correct in `.env`
2. Verify Cornell API endpoint is accessible
3. Check backend logs: `docker-compose logs backend`

**Error: "LITELLM_API_KEY environment variable is not set"**
- Make sure you added the key to `backend/.env`
- Rebuild backend: `docker-compose up -d --build backend`

### Yelp API Errors

**Error: "Invalid Yelp API key"**
- Verify your API key at https://www.yelp.com/developers
- Check it's correctly set in `backend/.env`

**Error: "Too many requests"**
- Yelp free tier has rate limits (5000 requests/day)
- Wait a few minutes before trying again

### Location Detection Issues

If location detection fails:
- Manually enter location in the input box
- Default fallback is "Ithaca, NY"

### No Recommendations Found

If chatbot says "couldn't find any restaurants":
- Try a different location
- Make your query more general
- Check if the cuisine type exists in your area

## Production Deployment

For production deployment:

### 1. Secure API Keys

**Don't commit API keys to Git!** Use environment variables or secrets manager:

```bash
# In production environment
export YELP_API_KEY=your_key
export LITELLM_API_KEY=your_key
```

### 2. Use HTTPS

- Get SSL certificate (Let's Encrypt)
- Configure Nginx for HTTPS
- Update CORS settings

### 3. Rate Limiting

Add rate limiting to prevent abuse:

```python
# In main.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@limiter.limit("10/minute")
@router.post("/api/chat/message")
async def send_message(...):
    ...
```

### 4. Caching

Cache LLM responses for common queries:

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_categories(query: str):
    # Cache category generation
    ...
```

### 5. Monitoring

- Add logging for all API calls
- Monitor Yelp API usage
- Track LLM token usage
- Set up error alerts

## Cost Estimation

### Yelp API
- **Free tier**: 5,000 requests/day
- **Cost**: $0 for most use cases

### LiteLLM (GPT-4o)
- Depends on your Cornell allocation
- Average: ~200 tokens per request
- Monitor usage to avoid exceeding limits

### IP Geolocation
- **ip-api.com free**: 45 requests/minute
- **Cost**: $0 for moderate usage

## Next Steps

1. ✅ Add your API keys to `.env`
2. ✅ Rebuild backend: `docker-compose up -d --build`
3. ✅ Test the chatbot at http://localhost
4. 📝 Customize the LLM prompts in `llm_service.py`
5. 🎨 Customize the UI in `Chatbot.css`
6. 🚀 Deploy to production (AWS, Google Cloud, etc.)

## Support

For issues or questions:
- Check backend logs: `docker-compose logs backend`
- Check database: `docker exec -it kindalike_db psql -U postgres -d kindalike`
- Review the main README.md and DOCKER_DEPLOYMENT.md

Enjoy your AI-powered restaurant finder!
