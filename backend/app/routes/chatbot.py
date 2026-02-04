from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.database import get_db_connection
from app.services.llm_service import generate_chat_response
import logging
from datetime import datetime
import json

# Configure logging
logger = logging.getLogger("app.routes.chatbot")

# Create the router instance
router = APIRouter()

# --- Pydantic Models ---
class ChatMessage(BaseModel):
    message: str
    session_id: Optional[int] = None

class ChatResponse(BaseModel):
    response: str
    session_id: int

class SessionInfo(BaseModel):
    id: Optional[int] = None
    session_id: int
    created_at: datetime
    started_at: Optional[datetime] = None
    last_message: Optional[str] = None
    message_count: Optional[int] = 0

# --- Routes ---

@router.get("/sessions", response_model=List[SessionInfo])
async def get_chat_sessions(authorization: Optional[str] = Header(None)):
    """
    Retrieve all chat sessions for the authenticated user.
    """
    # In production, use authorization to get the real user_id
    user_id = 1 
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Get sessions with their last message preview
        cur.execute("""
            SELECT cs.id, cs.created_at,
                   (SELECT content FROM chat_messages cm WHERE cm.session_id = cs.id ORDER BY cm.created_at DESC LIMIT 1) as last_message,
                   (SELECT COUNT(*) FROM chat_messages cm WHERE cm.session_id = cs.id) as message_count
            FROM chat_sessions cs
            WHERE cs.user_id = %s
            ORDER BY cs.updated_at DESC
        """, (user_id,))

        sessions = []
        for row in cur.fetchall():
            sessions.append({
                "id": row['id'],
                "session_id": row['id'],
                "created_at": row['created_at'],
                "started_at": row['created_at'],
                "last_message": row['last_message'] or "New Conversation",
                "message_count": row['message_count'] or 0
            })
            
        return sessions
    except Exception as e:
        logger.error(f"Error fetching sessions: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        cur.close()
        conn.close()


@router.get("/sessions/{session_id}/messages")
async def get_session_messages(session_id: int, authorization: Optional[str] = Header(None)):
    """Retrieve all messages for a given chat session."""
    user_id = 1
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Verify session belongs to user
        cur.execute("SELECT id FROM chat_sessions WHERE id = %s AND user_id = %s", (session_id, user_id))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Session not found")

        cur.execute("""
            SELECT role, content, created_at
            FROM chat_messages
            WHERE session_id = %s
            ORDER BY created_at ASC
        """, (session_id,))
        messages = [{"role": row['role'], "content": row['content'], "created_at": row['created_at']} for row in cur.fetchall()]
        return messages
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching messages: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        cur.close()
        conn.close()


@router.post("/sessions/new")
async def create_new_session(authorization: Optional[str] = Header(None)):
    """Create a new chat session."""
    user_id = 1
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO chat_sessions (user_id) VALUES (%s) RETURNING id, created_at", (user_id,))
        row = cur.fetchone()
        conn.commit()
        return {
            "id": row['id'],
            "session_id": row['id'],
            "created_at": row['created_at'],
            "started_at": row['created_at'],
            "last_message": "New Conversation",
            "message_count": 0
        }
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating session: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        cur.close()
        conn.close()


@router.post("/message", response_model=ChatResponse)
async def send_chat_message(chat_msg: ChatMessage, authorization: Optional[str] = Header(None)):
    """
    Main chat endpoint.
    """
    logger.info("="*80)
    logger.info(f"📨 Received chat message: '{chat_msg.message}'")

    user_id = 1
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # 1. Get or Create Session
        session_id = chat_msg.session_id

        if session_id:
            # Verify session exists
            cur.execute("SELECT id FROM chat_sessions WHERE id = %s AND user_id = %s", (session_id, user_id))
            if not cur.fetchone():
                logger.warning(f"Session {session_id} not found, creating new one")
                session_id = None

        if not session_id:
            logger.info("🔄 Creating new chat session...")
            cur.execute(
                "INSERT INTO chat_sessions (user_id) VALUES (%s) RETURNING id",
                (user_id,)
            )
            session_id = cur.fetchone()['id']
            conn.commit()

        logger.info(f"✅ Using session_id={session_id}")

        # 2. Fetch User Preferences (Using NEW DB Schema)
        logger.info(f"🔄 Fetching user preferences for user {user_id}...")
        
        # Query your new normalized table structure
        cur.execute("""
            SELECT category, subcategory, value_text, value_json, confidence_score
            FROM user_preferences 
            WHERE user_id = %s
        """, (user_id,))
        
        rows = cur.fetchall()
        
        # Transform DB rows into a clean dictionary for the LLM
        preferences_data = {
            "cuisines": [],
            "dietary_restrictions": [],
            "price_preference": "Any",
            "ambiance_preference": [],
            "flavor_profile": {},
            "general_notes": []
        }

        for row in rows:
            category = row['category']
            subcategory = row['subcategory']
            val_text = row['value_text']
            val_json = row['value_json']
            score = row['confidence_score']

            # Skip low confidence preferences
            if score is not None and score < 0.4:
                continue

            # Map DB categories to LLM JSON structure
            if category == 'cuisine' and val_text:
                preferences_data["cuisines"].append(val_text)
            elif category == 'dietary' and val_text:
                preferences_data["dietary_restrictions"].append(val_text)
            elif category == 'price' and val_text:
                preferences_data["price_preference"] = val_text
            elif category == 'ambiance' and val_text:
                preferences_data["ambiance_preference"].append(val_text)
            elif category == 'flavor' and subcategory:
                preferences_data["flavor_profile"][subcategory] = val_text
            elif category == 'general' and val_text:
                preferences_data["general_notes"].append(val_text)

        logger.info(f"✅ Loaded preferences: {len(rows)} records found")

        # 3. Fetch Chat History
        cur.execute("""
            SELECT role, content 
            FROM chat_messages 
            WHERE session_id = %s 
            ORDER BY created_at ASC
        """, (session_id,))
        
        history_rows = cur.fetchall()
        chat_history = [{"role": row['role'], "content": row['content']} for row in history_rows]

        # 4. Generate LLM Response
        logger.info("🤖 Calling LLM service...")
        
        ai_response_text = await generate_chat_response(
            message=chat_msg.message,
            history=chat_history,
            user_preferences=preferences_data
        )
        
        # 5. Save Conversation to DB
        # Save User Message
        cur.execute("""
            INSERT INTO chat_messages (session_id, role, content)
            VALUES (%s, 'user', %s)
        """, (session_id, chat_msg.message))
        
        # Save Assistant Response
        cur.execute("""
            INSERT INTO chat_messages (session_id, role, content)
            VALUES (%s, 'assistant', %s)
        """, (session_id, ai_response_text))
        
        # Update Session Timestamp
        cur.execute("""
            UPDATE chat_sessions 
            SET updated_at = CURRENT_TIMESTAMP 
            WHERE id = %s
        """, (session_id,))
        
        conn.commit()
        
        return ChatResponse(
            response=ai_response_text,
            session_id=session_id
        )

    except Exception as e:
        conn.rollback()
        logger.error(f"❌ Error processing message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()