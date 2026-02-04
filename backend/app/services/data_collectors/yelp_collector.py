"""
Yelp Fusion API Data Collector
Collects detailed restaurant data and reviews for preference extraction
"""
import os
import time
import requests
from typing import Dict, List, Any, Optional
from loguru import logger


class YelpCollector:
    """
    Collector for fetching detailed restaurant data from Yelp Fusion API.
    Includes business details, attributes, and reviews.
    """

    def __init__(self):
        """Initialize Yelp API collector"""
        self.api_key = os.getenv("YELP_API_KEY")
        if not self.api_key:
            raise ValueError("YELP_API_KEY environment variable is not set")

        self.base_url = "https://api.yelp.com/v3"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }

        # Rate limiting settings
        self.request_delay = 0.2  # 200ms between requests
        self.max_retries = 3
        self.last_request_time = 0

    def _rate_limit(self):
        """Enforce rate limiting between requests"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.request_delay:
            time.sleep(self.request_delay - elapsed)
        self.last_request_time = time.time()

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """
        Make a rate-limited request to Yelp API with retry logic

        Args:
            endpoint: API endpoint URL
            params: Query parameters

        Returns:
            Response JSON or None if all retries fail
        """
        for attempt in range(self.max_retries):
            self._rate_limit()

            try:
                response = requests.get(
                    endpoint,
                    headers=self.headers,
                    params=params,
                    timeout=15
                )

                if response.status_code == 429:
                    # Rate limited - exponential backoff
                    wait_time = (2 ** attempt) * 1
                    logger.warning(f"Yelp rate limited, waiting {wait_time}s before retry")
                    time.sleep(wait_time)
                    continue

                response.raise_for_status()
                return response.json()

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    logger.warning(f"Yelp business not found: {endpoint}")
                    return None
                elif e.response.status_code == 401:
                    logger.error("Invalid Yelp API key")
                    return None
                else:
                    logger.error(f"Yelp API HTTP error: {e}")
                    if attempt < self.max_retries - 1:
                        time.sleep(1)
                        continue
                    return None

            except requests.exceptions.RequestException as e:
                logger.error(f"Yelp API request failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(1)
                    continue
                return None

        return None

    def search_business(self, name: str, location: str) -> Optional[Dict[str, Any]]:
        """
        Search for a business by name and location

        Args:
            name: Restaurant name
            location: City, state or address

        Returns:
            Best matching business result or None
        """
        endpoint = f"{self.base_url}/businesses/search"
        params = {
            "term": name,
            "location": location,
            "categories": "restaurants,food",
            "limit": 5,
            "sort_by": "best_match"
        }

        logger.info(f"Searching Yelp for: {name} in {location}")
        result = self._make_request(endpoint, params)

        if not result or not result.get("businesses"):
            logger.warning(f"No Yelp results for: {name} in {location}")
            return None

        # Find best match by name similarity
        businesses = result["businesses"]
        best_match = None
        best_score = 0

        name_lower = name.lower().strip()
        for business in businesses:
            business_name = business.get("name", "").lower().strip()

            # Exact match
            if business_name == name_lower:
                best_match = business
                break

            # Partial match scoring
            if name_lower in business_name or business_name in name_lower:
                score = len(set(name_lower.split()) & set(business_name.split()))
                if score > best_score:
                    best_score = score
                    best_match = business

        if not best_match:
            # Fall back to first result
            best_match = businesses[0]
            logger.info(f"Using first Yelp result for: {name}")

        logger.info(f"Found Yelp match: {best_match.get('name')} (ID: {best_match.get('id')})")
        return best_match

    def get_business_details(self, business_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific business

        Args:
            business_id: Yelp business ID

        Returns:
            Detailed business information or None
        """
        endpoint = f"{self.base_url}/businesses/{business_id}"
        logger.info(f"Fetching Yelp business details: {business_id}")

        result = self._make_request(endpoint)
        if result:
            logger.info(f"Got Yelp details for: {result.get('name')}")
        return result

    def get_reviews(self, business_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get reviews for a business

        Note: Yelp API only returns up to 3 reviews per request.
        For more reviews, web scraping would be needed (not implemented here).

        Args:
            business_id: Yelp business ID
            limit: Maximum number of reviews (API max is 3)

        Returns:
            List of review objects
        """
        endpoint = f"{self.base_url}/businesses/{business_id}/reviews"
        params = {"limit": min(limit, 3)}  # Yelp only allows 3 reviews per request

        logger.info(f"Fetching Yelp reviews for: {business_id}")
        result = self._make_request(endpoint, params)

        if not result:
            return []

        reviews = result.get("reviews", [])
        logger.info(f"Got {len(reviews)} Yelp reviews")
        return reviews

    def collect_full_data(self, name: str, location: str) -> Dict[str, Any]:
        """
        Collect all available data for a restaurant

        Args:
            name: Restaurant name
            location: City, state or address

        Returns:
            Complete restaurant data including details and reviews
        """
        result = {
            "source": "yelp",
            "success": False,
            "errors": [],
            "business": None,
            "reviews": [],
            "attributes": {}
        }

        # Step 1: Search for the business
        search_result = self.search_business(name, location)
        if not search_result:
            result["errors"].append(f"Business not found: {name} in {location}")
            return result

        business_id = search_result.get("id")
        if not business_id:
            result["errors"].append("No business ID in search result")
            return result

        # Step 2: Get detailed business information
        details = self.get_business_details(business_id)
        if details:
            result["business"] = {
                "id": details.get("id"),
                "name": details.get("name"),
                "alias": details.get("alias"),
                "url": details.get("url"),
                "phone": details.get("phone"),
                "display_phone": details.get("display_phone"),
                "review_count": details.get("review_count"),
                "rating": details.get("rating"),
                "price": details.get("price"),
                "categories": [
                    {"alias": cat.get("alias"), "title": cat.get("title")}
                    for cat in details.get("categories", [])
                ],
                "location": {
                    "address1": details.get("location", {}).get("address1"),
                    "address2": details.get("location", {}).get("address2"),
                    "city": details.get("location", {}).get("city"),
                    "state": details.get("location", {}).get("state"),
                    "zip_code": details.get("location", {}).get("zip_code"),
                    "country": details.get("location", {}).get("country"),
                    "display_address": details.get("location", {}).get("display_address", [])
                },
                "coordinates": {
                    "latitude": details.get("coordinates", {}).get("latitude"),
                    "longitude": details.get("coordinates", {}).get("longitude")
                },
                "photos": details.get("photos", []),
                "hours": details.get("hours", []),
                "is_closed": details.get("is_closed", False),
                "transactions": details.get("transactions", [])
            }

            # Extract attributes/amenities
            result["attributes"] = {
                "outdoor_seating": "outdoor_seating" in details.get("transactions", []),
                "delivery": "delivery" in details.get("transactions", []),
                "pickup": "pickup" in details.get("transactions", []),
                "reservation": "restaurant_reservation" in details.get("transactions", [])
            }

            # If special_hours or messaging are available
            if details.get("special_hours"):
                result["attributes"]["has_special_hours"] = True
            if details.get("messaging"):
                result["attributes"]["supports_messaging"] = True

            result["success"] = True
        else:
            result["errors"].append("Failed to fetch business details")

        # Step 3: Get reviews
        reviews = self.get_reviews(business_id)
        result["reviews"] = [
            {
                "id": review.get("id"),
                "rating": review.get("rating"),
                "text": review.get("text"),
                "time_created": review.get("time_created"),
                "user": {
                    "name": review.get("user", {}).get("name"),
                    "image_url": review.get("user", {}).get("image_url")
                }
            }
            for review in reviews
        ]

        logger.info(f"Collected Yelp data for {name}: success={result['success']}, reviews={len(result['reviews'])}")
        return result


# Singleton instance
_yelp_collector_instance = None


def get_yelp_collector() -> YelpCollector:
    """Get or create the Yelp collector singleton"""
    global _yelp_collector_instance
    if _yelp_collector_instance is None:
        _yelp_collector_instance = YelpCollector()
    return _yelp_collector_instance
