"""
Preference Extractor Service
Orchestrates data collection from APIs and LLM analysis
"""
import time
import json
from typing import Dict, List, Any, Optional, Tuple
from loguru import logger
import psycopg2
from psycopg2.extras import RealDictCursor

from ..data_collectors.yelp_collector import get_yelp_collector
from ..data_collectors.google_collector import get_google_collector
from ..data_collectors.llm_analyzer import get_llm_analyzer


class PreferenceExtractor:
    """
    Main orchestrator for preference extraction.
    Collects data from Yelp, Google, and uses LLM to analyze reviews.
    """

    def __init__(self, db_connection):
        """
        Initialize the preference extractor

        Args:
            db_connection: Database connection object
        """
        self.conn = db_connection
        self.yelp_collector = get_yelp_collector()
        self.google_collector = get_google_collector()
        self.llm_analyzer = get_llm_analyzer()

    def get_user_initial_restaurants(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get the user's initial restaurant selections from the database

        Args:
            user_id: User ID

        Returns:
            List of restaurant records with their details
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT
                    uir.id as selection_id,
                    uir.selection_order,
                    uir.user_notes,
                    uir.favorite_dish,
                    r.id as restaurant_id,
                    r.name,
                    r.yelp_id,
                    r.google_place_id,
                    r.address,
                    r.city,
                    r.state,
                    r.price_level,
                    r.rating,
                    r.categories
                FROM user_initial_restaurants uir
                JOIN restaurants r ON uir.restaurant_id = r.id
                WHERE uir.user_id = %s
                ORDER BY uir.selection_order
            """, (user_id,))

            return [dict(row) for row in cur.fetchall()]

    def collect_restaurant_data(
        self,
        restaurant_id: int,
        name: str,
        location: str,
        yelp_id: Optional[str] = None,
        google_place_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Collect data from all sources for a single restaurant

        Args:
            restaurant_id: Database restaurant ID
            name: Restaurant name
            location: Restaurant location (city, state)
            yelp_id: Optional existing Yelp ID
            google_place_id: Optional existing Google Place ID

        Returns:
            Dict with collected data from all sources
        """
        result = {
            "restaurant_id": restaurant_id,
            "restaurant_name": name,
            "location": location,
            "yelp_data": None,
            "google_data": None,
            "combined_reviews": [],
            "llm_insights": None,
            "data_completeness": 0.0,
            "errors": []
        }

        # Step 1: Collect Yelp data
        logger.info(f"Collecting Yelp data for: {name}")
        try:
            yelp_data = self.yelp_collector.collect_full_data(name, location)
            if yelp_data is None:
                logger.warning(f"Yelp collector returned None for {name}")
                yelp_data = {"success": False, "errors": ["Yelp returned None"], "reviews": []}

            if yelp_data.get("success"):
                result["yelp_data"] = yelp_data
                # Add Yelp reviews to combined list
                reviews = yelp_data.get("reviews") or []
                logger.info(f"=== YELP REVIEWS for {name} ({len(reviews)} reviews) ===")
                for i, review in enumerate(reviews):
                    if review:
                        review_text = review.get("text", "")
                        review_rating = review.get("rating")
                        logger.info(f"  [{i+1}] Rating: {review_rating}/5")
                        logger.info(f"       {review_text[:300]}{'...' if len(review_text) > 300 else ''}")
                        result["combined_reviews"].append({
                            "source": "yelp",
                            "text": review_text,
                            "rating": review_rating
                        })
                logger.info(f"=== END YELP REVIEWS for {name} ===")
            else:
                errors = yelp_data.get("errors") or []
                result["errors"].extend(errors)
        except Exception as e:
            logger.error(f"Yelp collection error for {name}: {e}")
            result["errors"].append(f"Yelp error: {str(e)}")

        # Step 2: Collect Google data
        logger.info(f"Collecting Google data for: {name}")
        try:
            google_data = self.google_collector.collect_full_data(name, location)
            if google_data is None:
                logger.warning(f"Google collector returned None for {name}")
                google_data = {"success": False, "errors": ["Google returned None"], "reviews": []}

            if google_data.get("success"):
                result["google_data"] = google_data
                # Add Google reviews to combined list
                reviews = google_data.get("reviews") or []
                logger.info(f"=== GOOGLE REVIEWS for {name} ({len(reviews)} reviews) ===")
                for i, review in enumerate(reviews):
                    if review:
                        review_text = review.get("text", "")
                        review_rating = review.get("rating")
                        author = review.get("author_name", "Anonymous")
                        logger.info(f"  [{i+1}] {author} - Rating: {review_rating}/5")
                        logger.info(f"       {review_text[:300]}{'...' if len(review_text) > 300 else ''}")
                        result["combined_reviews"].append({
                            "source": "google",
                            "text": review_text,
                            "rating": review_rating
                        })
                logger.info(f"=== END GOOGLE REVIEWS for {name} ===")
            else:
                errors = google_data.get("errors") or []
                result["errors"].extend(errors)
        except Exception as e:
            logger.error(f"Google collection error for {name}: {e}")
            result["errors"].append(f"Google error: {str(e)}")

        # Step 3: Use LLM to analyze combined reviews
        if result["combined_reviews"]:
            logger.info(f"Analyzing {len(result['combined_reviews'])} reviews for: {name}")
            try:
                # Get category from Yelp or Google data
                category = self._get_restaurant_category(result)
                price_level = self._get_price_level(result)
                rating = self._get_rating(result)

                llm_insights = self.llm_analyzer.analyze_reviews(
                    reviews=result["combined_reviews"],
                    restaurant_name=name,
                    location=location,
                    category=category,
                    price_level=price_level,
                    rating=rating
                )
                result["llm_insights"] = llm_insights

                # Log LLM output
                logger.info(f"=== LLM INSIGHTS for {name} ===")
                logger.info(f"Cuisine: {llm_insights.get('cuisine_style')}")
                logger.info(f"Popular dishes: {llm_insights.get('popular_dishes')}")
                logger.info(f"Flavor profile: {llm_insights.get('flavor_profile')}")
                logger.info(f"Ambiance: {llm_insights.get('ambiance')}")
                logger.info(f"Service: {llm_insights.get('service_style')}")
                logger.info(f"Dining context: {llm_insights.get('dining_context')}")
                logger.info(f"Price perception: {llm_insights.get('price_perception')}")
                logger.info(f"Sentiment: {llm_insights.get('overall_sentiment')}")
                logger.info(f"Confidence: {llm_insights.get('confidence')}")
                logger.info(f"Evidence: {llm_insights.get('evidence_summary')}")
                logger.info(f"=== END LLM INSIGHTS for {name} ===")
            except Exception as e:
                logger.error(f"LLM analysis error for {name}: {e}")
                result["errors"].append(f"LLM error: {str(e)}")

        # Calculate data completeness
        result["data_completeness"] = self._calculate_completeness(result)

        logger.info(f"Data collection complete for {name}: completeness={result['data_completeness']:.2f}")
        return result

    def _get_restaurant_category(self, data: Dict) -> str:
        """Extract primary category from collected data"""
        # Try Yelp first
        yelp_data = data.get("yelp_data") or {}
        yelp_business = yelp_data.get("business") or {}
        if yelp_business.get("categories"):
            categories = yelp_business["categories"]
            if categories:
                return categories[0].get("title", "Restaurant")

        # Try Google
        google_data = data.get("google_data") or {}
        google_place = google_data.get("place") or {}
        if google_place.get("types"):
            types = google_place["types"]
            if types:
                return types[0].replace("_", " ").title()

        return "Restaurant"

    def _get_price_level(self, data: Dict) -> Optional[str]:
        """Extract price level from collected data"""
        # Try Yelp first (uses $, $$, etc.)
        yelp_data = data.get("yelp_data") or {}
        yelp_business = yelp_data.get("business") or {}
        if yelp_business.get("price"):
            return yelp_business["price"]

        # Try Google (uses 1-4 scale)
        google_data = data.get("google_data") or {}
        google_place = google_data.get("place") or {}
        if google_place.get("price_level"):
            level = google_place["price_level"]
            return "$" * level

        return None

    def _get_rating(self, data: Dict) -> Optional[float]:
        """Extract rating from collected data"""
        ratings = []

        yelp_data = data.get("yelp_data") or {}
        yelp_business = yelp_data.get("business") or {}
        if yelp_business.get("rating"):
            ratings.append(yelp_business["rating"])

        google_data = data.get("google_data") or {}
        google_place = google_data.get("place") or {}
        if google_place.get("rating"):
            ratings.append(google_place["rating"])

        return sum(ratings) / len(ratings) if ratings else None

    def _calculate_completeness(self, data: Dict) -> float:
        """
        Calculate data completeness score (0.0 to 1.0)

        Factors:
        - Yelp data available: 30%
        - Google data available: 30%
        - Reviews available: 25%
        - LLM insights available: 15%
        """
        score = 0.0

        yelp_data = data.get("yelp_data") or {}
        if yelp_data.get("success"):
            score += 0.30

        google_data = data.get("google_data") or {}
        if google_data.get("success"):
            score += 0.30

        # Reviews scoring (up to 25%)
        review_count = len(data.get("combined_reviews") or [])
        if review_count >= 5:
            score += 0.25
        elif review_count >= 3:
            score += 0.20
        elif review_count >= 1:
            score += 0.10

        # LLM insights (up to 15%)
        llm_insights = data.get("llm_insights") or {}
        if llm_insights:
            confidence = llm_insights.get("confidence", 0)
            score += 0.15 * confidence

        return min(score, 1.0)

    def extract_preferences(self, user_id: int) -> Dict[str, Any]:
        """
        Main method: Extract preferences for a user based on their initial restaurants

        Args:
            user_id: User ID

        Returns:
            Dict with all collected data for 3 restaurants
        """
        start_time = time.time()

        result = {
            "user_id": user_id,
            "status": "processing",
            "restaurants": [],
            "errors": [],
            "processing_duration_ms": 0
        }

        # Get user's initial restaurants
        restaurants = self.get_user_initial_restaurants(user_id)
        if not restaurants:
            result["status"] = "failed"
            result["errors"].append("No initial restaurants found for user")
            return result

        if len(restaurants) < 3:
            result["errors"].append(f"Only {len(restaurants)} restaurants found, expected 3")

        # Collect data for each restaurant
        for restaurant in restaurants:
            location = f"{restaurant.get('city', '')}, {restaurant.get('state', '')}"
            if not location.strip(", "):
                location = "USA"  # Fallback

            restaurant_data = self.collect_restaurant_data(
                restaurant_id=restaurant["restaurant_id"],
                name=restaurant["name"],
                location=location,
                yelp_id=restaurant.get("yelp_id"),
                google_place_id=restaurant.get("google_place_id")
            )

            # Add user-provided info
            restaurant_data["user_notes"] = restaurant.get("user_notes")
            restaurant_data["user_favorite_dish"] = restaurant.get("favorite_dish")
            restaurant_data["selection_order"] = restaurant.get("selection_order")

            result["restaurants"].append(restaurant_data)

        # Store raw data in preference_analyses table
        self._store_analysis_data(user_id, result["restaurants"])

        # Calculate processing time
        result["processing_duration_ms"] = int((time.time() - start_time) * 1000)
        result["status"] = "awaiting_questionnaire"

        logger.info(f"Preference extraction complete for user {user_id}: {result['processing_duration_ms']}ms")
        return result

    def _store_analysis_data(self, user_id: int, restaurants_data: List[Dict]):
        """
        Store the collected data in preference_analyses table

        Args:
            user_id: User ID
            restaurants_data: List of restaurant data dicts
        """
        restaurant_ids = [r["restaurant_id"] for r in restaurants_data]

        yelp_data = {
            r["restaurant_id"]: r.get("yelp_data")
            for r in restaurants_data
        }

        google_data = {
            r["restaurant_id"]: r.get("google_data")
            for r in restaurants_data
        }

        llm_insights = {
            r["restaurant_id"]: r.get("llm_insights")
            for r in restaurants_data
        }

        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO preference_analyses (
                    user_id, restaurant_ids, yelp_data, google_data, llm_insights,
                    processing_status
                )
                VALUES (%s, %s, %s, %s, %s, 'awaiting_questionnaire')
                ON CONFLICT (user_id)
                DO UPDATE SET
                    restaurant_ids = EXCLUDED.restaurant_ids,
                    yelp_data = EXCLUDED.yelp_data,
                    google_data = EXCLUDED.google_data,
                    llm_insights = EXCLUDED.llm_insights,
                    processing_status = 'awaiting_questionnaire',
                    created_at = CURRENT_TIMESTAMP
            """, (
                user_id,
                restaurant_ids,
                json.dumps(yelp_data),
                json.dumps(google_data),
                json.dumps(llm_insights)
            ))
            self.conn.commit()

        logger.info(f"Stored analysis data for user {user_id}")

    def get_extraction_status(self, user_id: int) -> Dict[str, Any]:
        """
        Get the current extraction status for a user

        Args:
            user_id: User ID

        Returns:
            Status dict with processing state
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT
                    processing_status,
                    restaurant_ids,
                    created_at,
                    completed_at,
                    processing_duration_ms,
                    error_message
                FROM preference_analyses
                WHERE user_id = %s
            """, (user_id,))

            row = cur.fetchone()
            if not row:
                return {
                    "status": "not_started",
                    "message": "No preference extraction started"
                }

            return {
                "status": row["processing_status"],
                "restaurant_ids": row["restaurant_ids"],
                "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                "completed_at": row["completed_at"].isoformat() if row["completed_at"] else None,
                "processing_duration_ms": row["processing_duration_ms"],
                "error_message": row["error_message"]
            }


# Factory function
def get_preference_extractor(db_connection) -> PreferenceExtractor:
    """Create a preference extractor instance"""
    return PreferenceExtractor(db_connection)
