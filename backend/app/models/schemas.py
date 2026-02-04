from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum


# ============================================
# Authentication Schemas
# ============================================

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


# ============================================
# Restaurant Schemas
# ============================================

class RestaurantBase(BaseModel):
    name: str
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    phone: Optional[str] = None
    price_level: Optional[int] = Field(None, ge=1, le=4)
    rating: Optional[float] = Field(None, ge=0, le=5)
    review_count: Optional[int] = 0
    categories: Optional[List[Dict[str, str]]] = None
    image_url: Optional[str] = None


class RestaurantCreate(RestaurantBase):
    yelp_id: Optional[str] = None
    google_place_id: Optional[str] = None
    yelp_url: Optional[str] = None
    google_url: Optional[str] = None
    website_url: Optional[str] = None


class RestaurantResponse(RestaurantBase):
    id: int
    yelp_id: Optional[str] = None
    google_place_id: Optional[str] = None
    yelp_url: Optional[str] = None
    google_url: Optional[str] = None
    website_url: Optional[str] = None
    created_at: datetime


class RestaurantSearchRequest(BaseModel):
    name: str = Field(..., min_length=1)
    location: str = Field(..., min_length=1)


class RestaurantSearchResult(BaseModel):
    yelp_id: Optional[str] = None
    google_place_id: Optional[str] = None
    name: str
    address: Optional[str] = None
    city: Optional[str] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    price_level: Optional[int] = None
    categories: Optional[List[str]] = None
    image_url: Optional[str] = None
    distance: Optional[float] = None


# ============================================
# User Initial Restaurants (Onboarding)
# ============================================

class InitialRestaurantSelection(BaseModel):
    """Single restaurant selection during onboarding"""
    yelp_id: Optional[str] = None
    google_place_id: Optional[str] = None
    name: str
    location: str  # City, state or address
    selection_order: int = Field(..., ge=1, le=3)
    user_notes: Optional[str] = None
    favorite_dish: Optional[str] = None


class OnboardingSubmission(BaseModel):
    """Complete onboarding submission with 3 restaurants"""
    restaurants: List[InitialRestaurantSelection] = Field(..., min_length=3, max_length=3)


class OnboardingResponse(BaseModel):
    success: bool
    message: str
    restaurant_ids: List[int]
    extraction_started: bool


# ============================================
# LLM Review Analysis Schemas
# ============================================

class FlavorProfile(BaseModel):
    spice_level: Optional[str] = None  # 'mild', 'medium', 'hot', 'very_hot'
    dominant_flavors: Optional[List[str]] = None  # ['savory', 'sweet', 'umami', etc.]
    sweetness: Optional[str] = None  # 'not_sweet', 'slightly_sweet', 'sweet'
    richness: Optional[str] = None  # 'light', 'moderate', 'rich'


class AmbianceProfile(BaseModel):
    formality: Optional[str] = None  # 'casual', 'smart_casual', 'formal'
    noise_level: Optional[str] = None  # 'quiet', 'moderate', 'loud', 'lively'
    lighting: Optional[str] = None  # 'dim', 'moderate', 'bright'
    decor_style: Optional[str] = None  # 'modern', 'traditional', 'rustic', etc.
    vibe: Optional[str] = None  # 'romantic', 'trendy', 'cozy', 'upscale'


class DiningContext(BaseModel):
    romantic: Optional[bool] = None
    family_friendly: Optional[bool] = None
    good_for_groups: Optional[bool] = None
    date_night: Optional[bool] = None
    business_meeting: Optional[bool] = None
    solo_dining: Optional[bool] = None
    special_occasion: Optional[bool] = None


class LLMRestaurantInsights(BaseModel):
    """Structured insights extracted by LLM from restaurant reviews"""
    cuisine_style: Optional[str] = None
    cuisine_subcategories: Optional[List[str]] = None
    popular_dishes: Optional[List[str]] = None
    flavor_profile: Optional[FlavorProfile] = None
    ambiance: Optional[AmbianceProfile] = None
    service_style: Optional[str] = None  # 'fast', 'attentive', 'formal', 'casual'
    dining_context: Optional[DiningContext] = None
    portion_size: Optional[str] = None  # 'small', 'moderate', 'generous'
    best_for: Optional[List[str]] = None  # ['lunch', 'dinner', 'brunch', 'late_night']
    dietary_accommodations: Optional[List[str]] = None  # ['vegetarian', 'vegan', 'gluten_free']
    standout_features: Optional[List[str]] = None
    price_perception: Optional[str] = None  # 'great_value', 'fair', 'expensive', 'worth_it'
    wait_time: Optional[str] = None  # 'no_wait', 'short', 'moderate', 'long'
    parking: Optional[str] = None  # 'easy', 'street', 'valet', 'difficult'
    overall_sentiment: Optional[str] = None  # 'positive', 'mixed', 'negative'
    confidence: Optional[float] = Field(None, ge=0, le=1)


# ============================================
# Questionnaire Schemas
# ============================================

class QuestionType(str, Enum):
    TEXT = "text"
    SINGLE_CHOICE = "single_choice"
    MULTI_CHOICE = "multi_choice"
    BOOLEAN = "boolean"
    RATING = "rating"


class QuestionOption(BaseModel):
    value: str
    label: str


class QuestionItem(BaseModel):
    question_id: str
    restaurant_id: Optional[int] = None
    restaurant_name: Optional[str] = None
    question_text: str
    question_type: QuestionType
    options: Optional[List[QuestionOption]] = None
    required: bool = True
    category: str  # 'dish', 'flavor', 'ambiance', 'occasion', 'dietary'


class QuestionnaireResponse(BaseModel):
    questions: List[QuestionItem]
    total_questions: int


class QuestionAnswer(BaseModel):
    question_id: str
    answer_value: Union[str, List[str], bool, int]


class QuestionnaireSubmission(BaseModel):
    answers: List[QuestionAnswer]


# ============================================
# Preference Schemas
# ============================================

class PreferenceCategory(str, Enum):
    CUISINE = "cuisine"
    PRICE = "price"
    AMBIANCE = "ambiance"
    FLAVOR = "flavor"
    DIETARY = "dietary"
    OCCASION = "occasion"
    SERVICE = "service"
    LOCATION = "location"
    QUALITY = "quality"


class UserPreference(BaseModel):
    """Single user preference with confidence and weight"""
    category: str
    subcategory: Optional[str] = None
    value_text: Optional[str] = None
    value_numeric: Optional[float] = None
    value_json: Optional[Dict[str, Any]] = None
    confidence_score: float = Field(0.5, ge=0, le=1)
    weight: float = Field(0.1, ge=0, le=1)
    source: str = "onboarding"
    derived_from_restaurants: Optional[List[int]] = None


class UserPreferenceResponse(UserPreference):
    id: int
    user_id: int
    created_at: datetime
    last_updated: datetime


class UserPreferencesProfile(BaseModel):
    """Complete user preference profile"""
    user_id: int
    preferences: List[UserPreferenceResponse]
    preference_summary: Optional[Dict[str, Any]] = None
    extraction_status: str
    last_updated: Optional[datetime] = None


# ============================================
# Preference Extraction Schemas
# ============================================

class ExtractionStatus(str, Enum):
    PENDING = "pending"
    COLLECTING_DATA = "collecting_data"
    ANALYZING = "analyzing"
    AWAITING_QUESTIONNAIRE = "awaiting_questionnaire"
    AGGREGATING = "aggregating"
    COMPLETED = "completed"
    FAILED = "failed"


class DataCollectionResult(BaseModel):
    """Result from collecting data for a single restaurant"""
    restaurant_id: int
    restaurant_name: str
    yelp_data: Optional[Dict[str, Any]] = None
    google_data: Optional[Dict[str, Any]] = None
    llm_insights: Optional[LLMRestaurantInsights] = None
    data_completeness: float = Field(0, ge=0, le=1)
    errors: Optional[List[str]] = None


class ExtractionProgressResponse(BaseModel):
    """Progress of preference extraction"""
    user_id: int
    status: ExtractionStatus
    current_step: str
    progress_percent: int = Field(0, ge=0, le=100)
    restaurants_processed: int = 0
    total_restaurants: int = 3
    message: str


class ExtractionResultResponse(BaseModel):
    """Complete extraction result"""
    user_id: int
    status: ExtractionStatus
    restaurant_data: List[DataCollectionResult]
    questionnaire: Optional[QuestionnaireResponse] = None
    preferences_extracted: int = 0
    processing_duration_ms: Optional[int] = None


class PreferenceExtractionRequest(BaseModel):
    """Request to start preference extraction"""
    force_refresh: bool = False


class PreferenceExtractionResponse(BaseModel):
    """Response after initiating extraction"""
    success: bool
    message: str
    status: ExtractionStatus
    questionnaire: Optional[QuestionnaireResponse] = None


# ============================================
# Aggregated Preference Schemas
# ============================================

class AggregatedPreference(BaseModel):
    """Aggregated preference from multiple restaurants"""
    category: str
    subcategory: Optional[str] = None
    values: List[str]  # Values from each restaurant
    consensus_value: Optional[str] = None
    consistency: str  # 'high', 'medium', 'low', 'exploratory'
    confidence_score: float
    weight: float
    source_restaurants: List[int]


class PreferenceSummary(BaseModel):
    """Summary of all user preferences"""
    user_id: int

    # Top-level preferences
    primary_cuisines: List[str]
    price_range: str
    preferred_ambiance: str
    flavor_preferences: FlavorProfile
    dietary_requirements: List[str]

    # Dining contexts
    prefers_for_dates: bool
    prefers_for_groups: bool
    prefers_for_family: bool

    # Quality indicators
    overall_confidence: float
    data_completeness: float
    preferences_count: int

    # Metadata
    derived_from_restaurants: List[int]
    last_updated: datetime


# ============================================
# Legacy Schemas (for backward compatibility)
# ============================================

class UserPreferences(BaseModel):
    """Legacy preference schema - deprecated"""
    cuisine_type: Optional[str] = None
    price_range: Optional[str] = None
    dining_style: Optional[str] = None
    dietary_restrictions: Optional[str] = None
    atmosphere: Optional[str] = None


class UserPreferencesResponseLegacy(UserPreferences):
    """Legacy preference response - deprecated"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
