from fastapi import APIRouter, HTTPException, status
from app.models.schemas import UserCreate, UserLogin, TokenResponse, UserResponse
from app.database import get_db_connection, close_db_connection
from app.utils import hash_password, verify_password, create_access_token
from datetime import datetime

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(user: UserCreate):
    """Register a new user"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if username already exists
        cursor.execute("SELECT id FROM users WHERE username = %s", (user.username,))
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )

        # Hash password and create user
        hashed_password = hash_password(user.password)
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (%s, %s) RETURNING id, username, created_at",
            (user.username, hashed_password)
        )
        new_user = cursor.fetchone()
        conn.commit()

        # Create JWT token
        token = create_access_token(new_user['id'], new_user['username'])

        user_response = UserResponse(
            id=new_user['id'],
            username=new_user['username'],
            created_at=new_user['created_at']
        )

        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user=user_response
        )

    except HTTPException:
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating user: {str(e)}"
        )
    finally:
        if conn:
            close_db_connection(conn)

@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    """Login user and return JWT token"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get user by username
        cursor.execute(
            "SELECT id, username, password_hash, created_at FROM users WHERE username = %s",
            (credentials.username,)
        )
        user = cursor.fetchone()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )

        # Verify password
        if not verify_password(credentials.password, user['password_hash']):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )

        # Create JWT token
        token = create_access_token(user['id'], user['username'])

        user_response = UserResponse(
            id=user['id'],
            username=user['username'],
            created_at=user['created_at']
        )

        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user=user_response
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during login: {str(e)}"
        )
    finally:
        if conn:
            close_db_connection(conn)
