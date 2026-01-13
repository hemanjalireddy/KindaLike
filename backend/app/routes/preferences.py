from fastapi import APIRouter, HTTPException, status, Header
from typing import Optional
from app.models.schemas import UserPreferences, UserPreferencesResponse
from app.database import get_db_connection, close_db_connection
from app.utils import decode_access_token

router = APIRouter(prefix="/api/preferences", tags=["Preferences"])

def get_current_user(authorization: Optional[str] = Header(None)):
    """Extract user from JWT token"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing"
        )

    try:
        # Extract token from "Bearer <token>" format
        token = authorization.split(" ")[1] if " " in authorization else authorization
        payload = decode_access_token(token)
        return payload['user_id']
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )

@router.post("/", response_model=UserPreferencesResponse, status_code=status.HTTP_201_CREATED)
async def create_or_update_preferences(
    preferences: UserPreferences,
    authorization: Optional[str] = Header(None)
):
    """Create or update user preferences"""
    user_id = get_current_user(authorization)
    conn = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if preferences already exist for this user
        cursor.execute(
            "SELECT id FROM user_preferences WHERE user_id = %s",
            (user_id,)
        )
        existing = cursor.fetchone()

        if existing:
            # Update existing preferences
            cursor.execute(
                """
                UPDATE user_preferences
                SET cuisine_type = %s,
                    price_range = %s,
                    dining_style = %s,
                    dietary_restrictions = %s,
                    atmosphere = %s
                WHERE user_id = %s
                RETURNING id, user_id, cuisine_type, price_range, dining_style,
                          dietary_restrictions, atmosphere, created_at, updated_at
                """,
                (
                    preferences.cuisine_type,
                    preferences.price_range,
                    preferences.dining_style,
                    preferences.dietary_restrictions,
                    preferences.atmosphere,
                    user_id
                )
            )
        else:
            # Insert new preferences
            cursor.execute(
                """
                INSERT INTO user_preferences
                (user_id, cuisine_type, price_range, dining_style, dietary_restrictions, atmosphere)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, user_id, cuisine_type, price_range, dining_style,
                          dietary_restrictions, atmosphere, created_at, updated_at
                """,
                (
                    user_id,
                    preferences.cuisine_type,
                    preferences.price_range,
                    preferences.dining_style,
                    preferences.dietary_restrictions,
                    preferences.atmosphere
                )
            )

        result = cursor.fetchone()
        conn.commit()

        return UserPreferencesResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving preferences: {str(e)}"
        )
    finally:
        if conn:
            close_db_connection(conn)

@router.get("/", response_model=UserPreferencesResponse)
async def get_preferences(authorization: Optional[str] = Header(None)):
    """Get user preferences"""
    user_id = get_current_user(authorization)
    conn = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, user_id, cuisine_type, price_range, dining_style,
                   dietary_restrictions, atmosphere, created_at, updated_at
            FROM user_preferences
            WHERE user_id = %s
            """,
            (user_id,)
        )
        result = cursor.fetchone()

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Preferences not found"
            )

        return UserPreferencesResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching preferences: {str(e)}"
        )
    finally:
        if conn:
            close_db_connection(conn)
