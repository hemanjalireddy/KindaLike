from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    username: str
    password: str

class UserPreferences(BaseModel):
    cuisine_type: Optional[str] = None
    price_range: Optional[str] = None
    dining_style: Optional[str] = None
    dietary_restrictions: Optional[str] = None
    atmosphere: Optional[str] = None

class UserPreferencesResponse(UserPreferences):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

class UserResponse(BaseModel):
    id: int
    username: str
    created_at: datetime

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse
