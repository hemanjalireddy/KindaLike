from fastapi import APIRouter, HTTPException, Depends, Header, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.database import get_db_connection
from app.services.data_collectors.yelp_collector import get_yelp_collector
from app.services.preference_extraction.preference_aggregator import PreferenceAggregator
from app.services.preference_extraction.preference_scorer import PreferenceScorer
from app.services.preference_extraction.questionnaire_generator import QuestionnaireGenerator

import logging
from datetime import datetime
import json
from psycopg2.extras import RealDictCursor

# Configure logging
logger = logging.getLogger("app.routes.preference_extraction")

router = APIRouter(prefix="/api/preferences", tags=["Preference Extraction"])

# --- Pydantic Models ---

class RestaurantInput(BaseModel):
    name: str
    location: str
    notes: Optional[str] = None
    yelp_id: Optional[str] = None # Added useful field

class OnboardingData(BaseModel):
    restaurants: List[RestaurantInput]

class OnboardingResponse(BaseModel):
    success: bool
    message: str
    next_step: str
    extraction_started: bool 

class PreferenceItem(BaseModel):
    category: str
    value: str
    confidence: float
    source: str
    detected_at: datetime

class PreferenceProfile(BaseModel):
    user_id: int
    preferences: List[PreferenceItem]

# --- Helper Functions ---

def run_extraction_pipeline(user_id: int, restaurant_names: List[str]):
    """
    Background task: runs the REAL extraction pipeline using Yelp, Google, and LLM.
    """
    from app.services.preference_extraction.preference_extractor import get_preference_extractor

    logger.info(f"⚙️ Running REAL extraction pipeline for user {user_id}")

    conn = get_db_connection()

    try:
        extractor = get_preference_extractor(conn)

        # 1. Run the full extraction (Yelp + Google + LLM analysis)
        extraction_result = extractor.extract_preferences(user_id)

        logger.info(f"Extraction result status: {extraction_result.get('status')}")
        logger.info(f"Restaurants processed: {len(extraction_result.get('restaurants', []))}")
        logger.info(f"Processing time: {extraction_result.get('processing_duration_ms')}ms")

        # 2. Save individual preferences from LLM insights to user_preferences table
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM user_preferences WHERE user_id = %s AND source = 'onboarding'", (user_id,))

            def save_pref(category, value, subcategory=None, score=0.85):
                if value:
                    cur.execute("""
                        INSERT INTO user_preferences (user_id, category, subcategory, value_text, confidence_score, source)
                        VALUES (%s, %s, %s, %s, %s, 'onboarding')
                        ON CONFLICT (user_id, category, subcategory) DO NOTHING
                    """, (user_id, category, subcategory, str(value), score))

            for restaurant_data in extraction_result.get("restaurants", []):
                insights = restaurant_data.get("llm_insights") or {}
                confidence = insights.get("confidence", 0.7)

                if insights.get("cuisine_style"):
                    save_pref("cuisine", insights["cuisine_style"], score=confidence)
                for sub in insights.get("cuisine_subcategories", []):
                    save_pref("cuisine", sub, subcategory="sub", score=confidence * 0.9)
                for dish in insights.get("popular_dishes", []):
                    save_pref("dish", dish, score=confidence * 0.8)

                flavor = insights.get("flavor_profile", {})
                if flavor.get("spice_level"):
                    save_pref("flavor", flavor["spice_level"], subcategory="spice", score=confidence)
                if flavor.get("richness"):
                    save_pref("flavor", flavor["richness"], subcategory="richness", score=confidence)

                ambiance = insights.get("ambiance", {})
                if ambiance.get("vibe"):
                    save_pref("ambiance", ambiance["vibe"], score=confidence)
                if ambiance.get("formality"):
                    save_pref("ambiance", ambiance["formality"], subcategory="formality", score=confidence)

                if insights.get("price_perception"):
                    save_pref("price", insights["price_perception"], score=confidence)
                if insights.get("service_style"):
                    save_pref("service", insights["service_style"], score=confidence)
                for dietary in insights.get("dietary_accommodations", []):
                    save_pref("dietary", dietary, score=confidence)

            # Update analysis status to completed
            cur.execute("""
                UPDATE preference_analyses
                SET processing_status = 'completed', completed_at = NOW()
                WHERE user_id = %s
            """, (user_id,))

            conn.commit()
            logger.info(f"✅ Real extraction complete and saved for user {user_id}")

        finally:
            cur.close()

    except Exception as e:
        logger.error(f"❌ Extraction pipeline failed: {e}", exc_info=True)
        try:
            conn.rollback()
        except Exception:
            pass
    finally:
        conn.close()

# --- Routes ---

@router.post("/search-restaurant")
async def find_restaurant(query: Dict[str, str]):
    """
    Proxy endpoint to search Yelp/Google for a restaurant name 
    """
    term = query.get("name")
    location = query.get("location", "Ithaca, NY")
    
    if not term:
        raise HTTPException(status_code=400, detail="Restaurant name required")
        
    try:
        # Use your existing collector
        collector = get_yelp_collector()
        result = collector.search_business(term, location)
        if result:
            # Transform Yelp data into the format the frontend expects
            biz = result
            transformed = {
                "yelp_id": biz.get("id"),
                "name": biz.get("name"),
                "image_url": biz.get("image_url"),
                "rating": biz.get("rating"),
                "price_level": len(biz["price"]) if biz.get("price") else None,
                "categories": [c.get("title") for c in biz.get("categories", [])],
                "address": ", ".join(biz.get("location", {}).get("display_address", [])),
            }
            return [transformed]
        else:
            return []
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return {"found": False, "error": str(e)}


@router.post("/onboarding", response_model=OnboardingResponse)
async def submit_onboarding(data: OnboardingData, background_tasks: BackgroundTasks, authorization: Optional[str] = Header(None)):
    """
    Process initial onboarding:
    1. Saves restaurants to DB (restaurants table & user_initial_restaurants).
    2. Triggers background extraction.
    """
    user_id = 1  # Hardcoded for dev

    logger.info(f"🚀 Starting onboarding for user {user_id}")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        restaurant_names = []
        
        # 1. Loop through submitted restaurants
        for idx, r in enumerate(data.restaurants):
            restaurant_names.append(r.name)
            
            # A. Cache Restaurant (Basic Info)
            # We use name+location as a poor-man's unique key if yelp_id is missing
            cur.execute("""
                INSERT INTO restaurants (name, city, address)
                VALUES (%s, %s, %s)
                ON CONFLICT (name) DO NOTHING 
                RETURNING id
            """, (r.name, "Ithaca", r.location)) # Simplified for MVP
            
            # Fetch the ID (either new or existing)
            row = cur.fetchone()
            if not row:
                cur.execute("SELECT id FROM restaurants WHERE name = %s", (r.name,))
                row = cur.fetchone()

            restaurant_id = row['id'] if row else None

            # B. Link to User
            if restaurant_id:
                cur.execute("""
                    INSERT INTO user_initial_restaurants (user_id, restaurant_id, selection_order, user_notes)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (user_id, restaurant_id) DO NOTHING
                """, (user_id, restaurant_id, idx + 1, r.notes))

        conn.commit()

        # 2. Trigger Extraction (Background Task)
        background_tasks.add_task(run_extraction_pipeline, user_id, restaurant_names)
        
        return {
            "success": True,
            "message": "Preferences extraction started.",
            "next_step": "chatbot",
            "extraction_started": True
        }

    except Exception as e:
        conn.rollback()
        logger.error(f"Onboarding error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()


@router.post("/extract")
async def start_extraction(authorization: Optional[str] = Header(None)):
    """
    Start or check preference extraction.
    Since onboarding already triggers extraction via background task,
    this returns the current status from the DB.
    """
    user_id = 1

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT processing_status, preference_summary
            FROM preference_analyses
            WHERE user_id = %s
        """, (user_id,))
        row = cur.fetchone()

        if row and row['processing_status'] == 'completed':
            return {
                "success": True,
                "message": "Extraction complete",
                "status": "completed",
                "questionnaire": None
            }
        else:
            return {
                "success": True,
                "message": "Extraction in progress",
                "status": row['processing_status'] if row else "pending",
                "questionnaire": None
            }
    except Exception as e:
        logger.error(f"Extraction status error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()


@router.get("/extraction-status")
async def get_extraction_status(authorization: Optional[str] = Header(None)):
    """Return current extraction progress."""
    user_id = 1

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT processing_status
            FROM preference_analyses
            WHERE user_id = %s
        """, (user_id,))
        row = cur.fetchone()

        if row:
            status = row['processing_status']
            progress = 100 if status == 'completed' else 50
        else:
            status = "pending"
            progress = 0

        return {
            "status": status,
            "progress_percent": progress,
            "message": status
        }
    except Exception as e:
        logger.error(f"Extraction status error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()


@router.get("/questionnaire")
async def get_questionnaire(authorization: Optional[str] = Header(None)):
    """Return questionnaire questions (placeholder - no questionnaire for now)."""
    return {"questions": [], "total_questions": 0}


@router.post("/questionnaire")
async def submit_questionnaire_answers(body: Dict[str, Any], authorization: Optional[str] = Header(None)):
    """Accept questionnaire answers (placeholder)."""
    return {"success": True, "message": "Questionnaire submitted"}


@router.get("/profile", response_model=PreferenceProfile)
async def get_preference_profile(authorization: Optional[str] = Header(None)):
    """
    Get the summary of the user's extracted preferences.
    """
    user_id = 1
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor) # Use RealDictCursor for safety
    
    try:
        cur.execute("""
            SELECT category, value_text as value, confidence_score as confidence, updated_at
            FROM user_preferences
            WHERE user_id = %s
            ORDER BY category, confidence_score DESC
        """, (user_id,))
        
        rows = cur.fetchall()
        
        preferences = []
        for row in rows:
            preferences.append({
                "category": row['category'],
                "value": row['value'],
                "confidence": float(row['confidence']) if row['confidence'] else 0.0,
                "source": "inference", 
                "detected_at": row['updated_at']
            })
            
        return {
            "user_id": user_id,
            "preferences": preferences
        }
        
    except Exception as e:
        logger.error(f"Profile fetch error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()