"""
Yelp API Service for Restaurant Search
Integrates with Yelp Fusion API to search for restaurants
"""
import os
import requests
from typing import Dict, List, Any, Optional
from loguru import logger


class YelpService:
    """Service for searching restaurants using Yelp Fusion API"""

    def __init__(self):
        """Initialize Yelp API service"""
        self.api_key = os.getenv("YELP_API_KEY")
        if not self.api_key:
            raise ValueError("YELP_API_KEY environment variable is not set")

        self.base_url = "https://api.yelp.com/v3"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }

    def search_restaurants(
        self,
        location: str,
        categories: Optional[List[str]] = None,
        price: Optional[List[int]] = None,
        term: Optional[str] = None,
        attributes: Optional[List[str]] = None,
        limit: int = 10,
        offset: int = 0,
        sort_by: str = "best_match"
    ) -> Dict[str, Any]:
        """
        Search for restaurants using Yelp API

        Args:
            location: City or address to search in (e.g., "Ithaca, NY")
            categories: List of Yelp category aliases (e.g., ["italian", "pizza"])
            price: List of price levels 1-4 (e.g., [2, 3] for $$ and $$$)
            term: Search term (e.g., "pasta", "romantic dinner")
            attributes: List of attributes (e.g., ["hot_and_new", "reservation"])
            limit: Number of results to return (max 50)
            offset: Offset for pagination
            sort_by: Sort results by "best_match", "rating", "review_count", or "distance"

        Returns:
            Dict with 'businesses' list and 'total' count
        """
        endpoint = f"{self.base_url}/businesses/search"

        # Build query parameters
        params = {
            "location": location,
            "limit": min(limit, 50),  # Yelp max is 50
            "offset": offset,
            "sort_by": sort_by
        }

        # Add optional parameters
        if categories:
            params["categories"] = ",".join(categories)

        if price:
            # Convert list of integers to comma-separated string
            params["price"] = ",".join(str(p) for p in price if 1 <= p <= 4)

        if term:
            params["term"] = term

        if attributes:
            params["attributes"] = ",".join(attributes)

        logger.info(f"🌐 Yelp API Request: {endpoint}")
        logger.info(f"🌐 Params: {params}")

        try:
            response = requests.get(endpoint, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            result = response.json()
            logger.info(f"✅ Yelp API returned {result.get('total', 0)} total results, {len(result.get('businesses', []))} businesses in response")
            return result

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400:
                error_details = e.response.json()
                logger.error(f"❌ Yelp API 400 Bad Request: {error_details}")
                return {
                    "error": "Invalid request parameters",
                    "details": error_details,
                    "businesses": [],
                    "total": 0
                }
            elif e.response.status_code == 401:
                logger.error("❌ Yelp API 401 Unauthorized - Invalid API key")
                return {
                    "error": "Invalid Yelp API key",
                    "businesses": [],
                    "total": 0
                }
            else:
                logger.error(f"❌ Yelp API error {e.response.status_code}: {e}")
                return {
                    "error": f"Yelp API error: {e.response.status_code}",
                    "businesses": [],
                    "total": 0
                }
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Yelp API request failed: {str(e)}")
            return {
                "error": f"Request failed: {str(e)}",
                "businesses": [],
                "total": 0
            }

    def get_business_details(self, business_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific business

        Args:
            business_id: Yelp business ID

        Returns:
            Dict with business details or None if error
        """
        endpoint = f"{self.base_url}/businesses/{business_id}"

        try:
            response = requests.get(endpoint, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching business details: {e}")
            return None

    def search_with_llm_params(
        self,
        location: str,
        llm_categories: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Search for restaurants using parameters generated by LLM

        Args:
            location: City or address to search in
            llm_categories: Output from LLMService.generate_categories()
            user_preferences: User's saved preferences
            limit: Number of results to return

        Returns:
            Yelp search results
        """
        # Extract attributes from LLM output
        attributes = llm_categories.get("attributes", {})
        primary_categories = llm_categories.get("primary_categories", [])
        logger.info(f"🔍 Parsing LLM params - attributes: {attributes}")
        logger.info(f"🔍 Primary categories: {primary_categories}")

        # Determine price level
        price = None
        if attributes.get("price_level"):
            # Convert to integer if it's a string
            try:
                price_val = int(attributes["price_level"]) if isinstance(attributes["price_level"], str) else attributes["price_level"]
                if 1 <= price_val <= 4:
                    price = [price_val]
            except (ValueError, TypeError):
                pass  # Invalid price level, ignore it

        if not price and user_preferences and user_preferences.get("price_range"):
            # Convert price_range from user preferences
            price_map = {"$": [1], "$$": [2], "$$$": [3], "$$$$": [4]}
            price = price_map.get(user_preferences["price_range"], [2])

        # Build search term from cuisine and keywords
        term_parts = []
        if attributes.get("cuisine_type"):
            term_parts.append(attributes["cuisine_type"])

        # Add ambiance keywords
        ambiance = attributes.get("ambiance_keywords", [])
        if ambiance:
            term_parts.extend(ambiance[:2])  # Use top 2 keywords

        term = " ".join(term_parts) if term_parts else None

        logger.info(f"🔍 Extracted price: {price}")
        logger.info(f"🔍 Extracted search term: {term}")

        # Build Yelp attributes list
        yelp_attributes = []
        special_features = attributes.get("special_features", [])

        # Map special features to Yelp attributes
        feature_map = {
            "reservations": "reservation",
            "outdoor seating": "outdoor_seating",
            "takeout": "restaurant_takeout",
            "delivery": "restaurant_delivery",
            "wheelchair accessible": "wheelchair_accessible",
            "good for groups": "good_for_groups",
            "hot and new": "hot_and_new"
        }

        for feature in special_features:
            feature_lower = feature.lower()
            if feature_lower in feature_map:
                yelp_attributes.append(feature_map[feature_lower])

        logger.info(f"🔍 Yelp attributes: {yelp_attributes}")
        logger.info(f"📞 Calling Yelp API with: location={location}, categories={primary_categories}, price={price}, term={term}")

        # Perform search
        return self.search_restaurants(
            location=location,
            categories=primary_categories if primary_categories else None,
            price=price,
            term=term,
            attributes=yelp_attributes if yelp_attributes else None,
            limit=limit,
            sort_by="best_match"
        )

    def format_restaurant_for_display(self, business: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format a Yelp business result for user-friendly display

        Args:
            business: Raw business object from Yelp API

        Returns:
            Formatted restaurant info
        """
        return {
            "id": business.get("id"),
            "name": business.get("name"),
            "rating": business.get("rating"),
            "review_count": business.get("review_count"),
            "price": business.get("price", "N/A"),
            "categories": [cat["title"] for cat in business.get("categories", [])],
            "address": " ".join(business.get("location", {}).get("display_address", [])),
            "phone": business.get("display_phone", "N/A"),
            "image_url": business.get("image_url"),
            "url": business.get("url"),
            "distance": round(business.get("distance", 0) * 0.000621371, 2),  # Convert meters to miles
            "is_closed": business.get("is_closed", False)
        }


# Singleton instance
_yelp_service_instance = None


def get_yelp_service() -> YelpService:
    """Get or create the Yelp service singleton"""
    global _yelp_service_instance
    if _yelp_service_instance is None:
        _yelp_service_instance = YelpService()
    return _yelp_service_instance
