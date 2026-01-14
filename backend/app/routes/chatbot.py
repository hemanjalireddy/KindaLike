"""
Chatbot API endpoints for restaurant recommendations
"""
from fastapi import APIRouter, Header, Request, HTTPException
from typing import Optional, List
from pydantic import BaseModel
import json
from loguru import logger

from ..database import get_db_connection
from ..utils import get_current_user
from ..services.llm_service import get_llm_service
from ..services.yelp_service import get_yelp_service
from ..services.location_service import get_location_service


router = APIRouter(prefix="/api/chat", tags=["chatbot"])


# Request/Response Models
class ChatMessageRequest(BaseModel):
    """Request body for sending a chat message"""
    message: str
    session_id: Optional[int] = None
    location: Optional[str] = None  # Optional manual location override


class ChatMessageResponse(BaseModel):
    """Response for a chat message"""
    session_id: int
    message_id: int
    response: str
    recommendations: Optional[List[dict]] = None


class ChatSessionResponse(BaseModel):
    """Response for a chat session"""
    id: int
    started_at: str
    last_message_at: str
    is_active: bool
    message_count: int


@router.post("/message", response_model=ChatMessageResponse)
async def send_chat_message(
    request: Request,
    chat_request: ChatMessageRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Send a chat message and get restaurant recommendations

    Flow:
    1. Get user ID from JWT token
    2. Get or create chat session
    3. Detect user location from IP (if not provided)
    4. Get user preferences from database
    5. Use LLM to generate search categories
    6. Search Yelp API for restaurants
    7. Save user message and assistant response to database
    8. Return recommendations
    """
    logger.info("=" * 80)
    logger.info(f"📨 Received chat message: '{chat_request.message}'")

    # Authenticate user
    user_id = get_current_user(authorization)
    logger.info(f"✅ User authenticated: user_id={user_id}")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Step 1: Get or create chat session
        logger.info("🔄 Step 1: Getting or creating chat session...")
        if chat_request.session_id:
            # Use existing session
            cursor.execute(
                "SELECT id FROM chat_sessions WHERE id = %s AND user_id = %s AND is_active = TRUE",
                (chat_request.session_id, user_id)
            )
            session = cursor.fetchone()
            if not session:
                raise HTTPException(status_code=404, detail="Chat session not found or inactive")
            session_id = session['id']
        else:
            # Create new session
            cursor.execute(
                "INSERT INTO chat_sessions (user_id) VALUES (%s) RETURNING id",
                (user_id,)
            )
            session_id = cursor.fetchone()['id']
            conn.commit()

        logger.info(f"✅ Using session_id={session_id}")

        # Step 2: Get user preferences
        logger.info("🔄 Step 2: Fetching user preferences...")
        cursor.execute(
            "SELECT cuisine_type, price_range, dining_style, dietary_restrictions, atmosphere FROM user_preferences WHERE user_id = %s",
            (user_id,)
        )
        prefs_row = cursor.fetchone()
        user_preferences = dict(prefs_row) if prefs_row else {}
        logger.info(f"✅ User preferences: {user_preferences}")

        # Step 3: Detect location
        logger.info("🔄 Step 3: Detecting location...")
        location = chat_request.location
        if not location:
            # Get location from IP
            location_service = get_location_service()

            # Extract IP from request headers
            client_ip = location_service.extract_ip_from_request(dict(request.headers))

            # Get location info
            location_info = location_service.get_location_from_ip(client_ip)
            location = location_info.get("formatted_location", "Ithaca, NY")

        logger.info(f"✅ Using location: {location}")

        # Step 4: Save user message to database
        logger.info("🔄 Step 4: Saving user message to database...")
        cursor.execute(
            "INSERT INTO chat_messages (session_id, role, content) VALUES (%s, %s, %s) RETURNING id",
            (session_id, "user", chat_request.message)
        )
        user_message_id = cursor.fetchone()['id']
        conn.commit()
        logger.info(f"✅ User message saved with id={user_message_id}")

        # Step 5: Generate categories with LLM
        logger.info("🔄 Step 5: Generating categories with LLM...")
        llm_service = get_llm_service()
        llm_result = llm_service.generate_categories(
            query=chat_request.message,
            user_preferences=user_preferences
        )
        logger.info(f"✅ LLM generated categories: {json.dumps(llm_result, indent=2)}")

        # Step 6: Search Yelp for restaurants
        logger.info("🔄 Step 6: Searching Yelp for restaurants...")
        yelp_service = get_yelp_service()
        yelp_results = yelp_service.search_with_llm_params(
            location=location,
            llm_categories=llm_result,
            user_preferences=user_preferences,
            limit=5  # Return top 5 recommendations
        )
        logger.info(f"✅ Yelp returned {len(yelp_results.get('businesses', []))} results")
        logger.debug(f"Yelp raw results: {json.dumps(yelp_results, indent=2)}")

        # Step 7: Format recommendations
        logger.info("🔄 Step 7: Formatting recommendations...")
        recommendations = []
        if "businesses" in yelp_results and yelp_results["businesses"]:
            for business in yelp_results["businesses"]:
                formatted = yelp_service.format_restaurant_for_display(business)
                recommendations.append(formatted)

        logger.info(f"✅ Formatted {len(recommendations)} recommendations")

        # Step 8: Generate response message
        logger.info("🔄 Step 8: Generating response message...")
        if recommendations:
            response_text = f"Based on your request for '{chat_request.message}' in {location}, here are my top recommendations:"
        else:
            response_text = f"I couldn't find any restaurants matching '{chat_request.message}' in {location}. Try adjusting your search or location."

        logger.info(f"✅ Response: {response_text}")

        # Step 9: Save assistant response to database
        logger.info("🔄 Step 9: Saving assistant response to database...")
        cursor.execute(
            """INSERT INTO chat_messages (session_id, role, content, recommendations)
               VALUES (%s, %s, %s, %s) RETURNING id""",
            (session_id, "assistant", response_text, json.dumps(recommendations) if recommendations else None)
        )
        assistant_message_id = cursor.fetchone()['id']
        conn.commit()
        logger.info(f"✅ Assistant response saved with id={assistant_message_id}")

        logger.info("🎉 Chat request completed successfully!")
        logger.info("=" * 80)

        return ChatMessageResponse(
            session_id=session_id,
            message_id=assistant_message_id,
            response=response_text,
            recommendations=recommendations
        )

    except Exception as e:
        logger.error(f"❌ Error processing message: {str(e)}")
        logger.exception(e)
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")
    finally:
        cursor.close()
        conn.close()


@router.get("/sessions", response_model=List[ChatSessionResponse])
async def get_chat_sessions(authorization: Optional[str] = Header(None)):
    """
    Get all chat sessions for the current user
    """
    user_id = get_current_user(authorization)

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """SELECT
                cs.id,
                cs.started_at,
                cs.last_message_at,
                cs.is_active,
                COUNT(cm.id) as message_count
               FROM chat_sessions cs
               LEFT JOIN chat_messages cm ON cs.id = cm.session_id
               WHERE cs.user_id = %s
               GROUP BY cs.id, cs.started_at, cs.last_message_at, cs.is_active
               ORDER BY cs.last_message_at DESC""",
            (user_id,)
        )
        sessions = cursor.fetchall()

        return [
            ChatSessionResponse(
                id=session['id'],
                started_at=session['started_at'].isoformat(),
                last_message_at=session['last_message_at'].isoformat(),
                is_active=session['is_active'],
                message_count=session['message_count']
            )
            for session in sessions
        ]

    finally:
        cursor.close()
        conn.close()


@router.post("/sessions/new")
async def create_new_session(authorization: Optional[str] = Header(None)):
    """
    Create a new chat session
    """
    user_id = get_current_user(authorization)

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO chat_sessions (user_id) VALUES (%s) RETURNING id, started_at, last_message_at, is_active",
            (user_id,)
        )
        session = cursor.fetchone()
        conn.commit()

        return ChatSessionResponse(
            id=session['id'],
            started_at=session['started_at'].isoformat(),
            last_message_at=session['last_message_at'].isoformat(),
            is_active=session['is_active'],
            message_count=0
        )

    finally:
        cursor.close()
        conn.close()


@router.get("/sessions/{session_id}/messages")
async def get_session_messages(
    session_id: int,
    authorization: Optional[str] = Header(None)
):
    """
    Get all messages for a specific chat session
    """
    user_id = get_current_user(authorization)

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Verify session belongs to user
        cursor.execute(
            "SELECT id FROM chat_sessions WHERE id = %s AND user_id = %s",
            (session_id, user_id)
        )
        session = cursor.fetchone()
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")

        # Get messages
        cursor.execute(
            """SELECT id, role, content, recommendations, created_at
               FROM chat_messages
               WHERE session_id = %s
               ORDER BY created_at ASC""",
            (session_id,)
        )
        messages = cursor.fetchall()

        return [
            {
                "id": msg['id'],
                "role": msg['role'],
                "content": msg['content'],
                "recommendations": msg['recommendations'],
                "created_at": msg['created_at'].isoformat()
            }
            for msg in messages
        ]

    finally:
        cursor.close()
        conn.close()


@router.delete("/sessions/{session_id}")
async def deactivate_session(
    session_id: int,
    authorization: Optional[str] = Header(None)
):
    """
    Deactivate a chat session (soft delete)
    """
    user_id = get_current_user(authorization)

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "UPDATE chat_sessions SET is_active = FALSE WHERE id = %s AND user_id = %s RETURNING id",
            (session_id, user_id)
        )
        result = cursor.fetchone()
        conn.commit()

        if not result:
            raise HTTPException(status_code=404, detail="Chat session not found")

        return {"message": "Chat session deactivated successfully"}

    finally:
        cursor.close()
        conn.close()
