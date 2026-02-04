"""
Google Places API Data Collector (New API)
Collects supplementary restaurant data, reviews, and photos using the new Places API
"""
import os
import time
import requests
from typing import Dict, List, Any, Optional
from loguru import logger


class GooglePlacesCollector:
    """
    Collector for fetching restaurant data from Google Places API (New).
    Provides supplementary reviews, photos, and additional metadata.
    """

    def __init__(self):
        """Initialize Google Places API collector"""
        self.api_key = os.getenv("GOOGLE_PLACES_API_KEY")
        if not self.api_key:
            logger.warning("GOOGLE_PLACES_API_KEY not set - Google Places collector will be disabled")
            self.enabled = False
        else:
            self.enabled = True

        # New Places API base URL
        self.base_url = "https://places.googleapis.com/v1"

        # Rate limiting settings
        self.request_delay = 0.1  # 100ms between requests
        self.max_retries = 3
        self.last_request_time = 0

    def _rate_limit(self):
        """Enforce rate limiting between requests"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.request_delay:
            time.sleep(self.request_delay - elapsed)
        self.last_request_time = time.time()

    def _make_request(self, endpoint: str, method: str = "GET", 
                      params: Optional[Dict] = None, json_data: Optional[Dict] = None,
                      field_mask: str = "*") -> Optional[Dict]:
        """
        Make a rate-limited request to Google Places API with retry logic

        Args:
            endpoint: API endpoint URL
            method: HTTP method (GET or POST)
            params: Query parameters
            json_data: JSON body data (for POST requests)
            field_mask: FieldMask for specifying which fields to return (required by new API)

        Returns:
            Response JSON or None if all retries fail
        """
        if not self.enabled:
            return None

        # Set up headers with API key and FieldMask (required by new API)
        headers = {
            "X-Goog-Api-Key": self.api_key,
            "Content-Type": "application/json",
            "X-Goog-FieldMask": field_mask
        }

        for attempt in range(self.max_retries):
            self._rate_limit()

            try:
                if method == "POST":
                    response = requests.post(endpoint, json=json_data, headers=headers, timeout=15)
                else:
                    response = requests.get(endpoint, params=params, headers=headers, timeout=15)
                
                # New API uses HTTP status codes for errors
                if response.status_code != 200:
                    # Log the full error for debugging
                    logger.error(f"Google Places Error ({response.status_code}): {response.text}")

                response.raise_for_status()
                result = response.json()
                return result

            except requests.exceptions.HTTPError as e:
                if response.status_code == 429:  # Rate limited
                    wait_time = (2 ** attempt) * 1
                    logger.warning(f"Google Places rate limited, waiting {wait_time}s")
                    time.sleep(wait_time)
                    continue
                elif response.status_code == 403:
                    error_msg = response.json().get("error", {}).get("message", "Access denied")
                    logger.error(f"Google Places request denied: {error_msg}")
                    return None
                elif response.status_code == 400:
                    error_msg = response.json().get("error", {}).get("message", "Invalid request")
                    logger.error(f"Google Places invalid request: {error_msg}")
                    return None
                else:
                    logger.error(f"Google Places HTTP error {response.status_code}: {e}")
                    if attempt < self.max_retries - 1:
                        time.sleep(1)
                        continue
                    return None

            except requests.exceptions.RequestException as e:
                logger.error(f"Google Places request failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(1)
                    continue
                return None

        return None

    def find_place(self, name: str, location: str) -> Optional[Dict[str, Any]]:
        """
        Find a place by name and location using Text Search API

        Args:
            name: Restaurant name
            location: City, state or address

        Returns:
            Place candidate with place_id or None
        """
        if not self.enabled:
            return None

        endpoint = f"{self.base_url}/places:searchText"
        
        # Prepare request body for new API
        request_body = {
            "textQuery": f"{name} in {location}",
            "pageSize": 1
        }

        # FieldMask for search text requests (POST to searchText requires "places." prefix)
        field_mask = "places.id,places.displayName,places.formattedAddress"

        logger.info(f"Searching Google Places for: {name} in {location}")
        result = self._make_request(endpoint, method="POST", json_data=request_body, field_mask=field_mask)

        if not result or "places" not in result or len(result["places"]) == 0:
            logger.warning(f"No Google Places results for: {name} in {location}")
            return None

        place = result["places"][0]
        # The 'id' field contains the place ID
        place_id = place.get("id") or place.get("name", "").replace("places/", "")
        logger.info(f"Found Google place: {place.get('displayName', {}).get('text')} (ID: {place_id})")

        # Add the id to the place dict for easier access
        place["place_id"] = place_id
        return place

    def get_place_details(self, place_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a place

        Args:
            place_id: Google Place ID (format: "places/{id}")

        Returns:
            Detailed place information or None
        """
        if not self.enabled:
            return None

        # Ensure place_id has the correct format
        if not place_id.startswith("places/"):
            place_id = f"places/{place_id}"

        endpoint = f"{self.base_url}/{place_id}"
        
        # FieldMask for detailed place requests - all fields we need
        # FIX: 'openingHours' -> 'regularOpeningHours' (New API standard)
        # Added 'id' explicitly
        field_mask = (
            "id,displayName,formattedAddress,internationalPhoneNumber,nationalPhoneNumber,"
            "types,websiteUri,rating,userRatingCount,reviews,photos,regularOpeningHours,"
            "businessStatus,location,priceLevel,reservable,dineIn,delivery,takeout,"
            "servesBreakfast,servesBrunch,servesLunch,servesDinner,servesVegetarianFood"
        )
        
        params = {}

        logger.info(f"Fetching Google place details: {place_id}")
        result = self._make_request(endpoint, method="GET", params=params, field_mask=field_mask)

        if not result:
            return None

        logger.info(f"Got Google details for: {result.get('displayName', {}).get('text')}")
        return result

    def get_reviews(self, place_id: str) -> List[Dict[str, Any]]:
        """
        Get reviews for a place (included in place details)
        """
        details = self.get_place_details(place_id)
        if not details:
            return []

        reviews = details.get("reviews", [])
        logger.info(f"Got {len(reviews)} Google reviews for place {place_id}")
        return reviews

    def get_photo_url(self, photo_name: str, max_width: int = 400) -> Optional[str]:
        """
        Generate a photo URL from photo name
        """
        if not self.enabled or not photo_name:
            return None

        return (
            f"{self.base_url}/{photo_name}/media"
            f"?maxWidthPx={max_width}"
            f"&key={self.api_key}"
        )

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
            "source": "google",
            "success": False,
            "errors": [],
            "place": None,
            "reviews": [],
            "photos": [],
            "attributes": {}
        }

        if not self.enabled:
            result["errors"].append("Google Places API not configured")
            return result

        # Step 1: Find the place
        place_search = self.find_place(name, location)
        if not place_search:
            result["errors"].append(f"Place not found: {name} in {location}")
            return result

        place_id = place_search.get("place_id") or place_search.get("id") or place_search.get("name")
        if not place_id:
            result["errors"].append("No place ID in search result")
            return result

        # Step 2: Get detailed place information
        details = self.get_place_details(place_id)
        if details:
            display_name = details.get("displayName", {})
            location_info = details.get("location", {})
            # FIX: Use 'regularOpeningHours' instead of 'openingHours'
            opening_hours = details.get("regularOpeningHours", {})
            
            result["place"] = {
                "place_id": details.get("id") or details.get("name"),
                "name": display_name.get("text"),
                "formatted_address": details.get("formattedAddress"),
                "phone": details.get("nationalPhoneNumber"),
                "international_phone": details.get("internationalPhoneNumber"),
                "website": details.get("websiteUri"),
                "rating": details.get("rating"),
                "user_ratings_total": details.get("userRatingCount"),
                "price_level": details.get("priceLevel"),
                "types": details.get("types", []),
                "business_status": details.get("businessStatus"),
                "geometry": {
                    "lat": location_info.get("latitude"),
                    "lng": location_info.get("longitude")
                },
                "opening_hours": {
                    "weekday_text": opening_hours.get("weekdayDescriptions", [])
                }
            }

            # Extract service attributes
            result["attributes"] = {
                "reservable": details.get("reservable"),
                "serves_breakfast": details.get("servesBreakfast"),
                "serves_brunch": details.get("servesBrunch"),
                "serves_lunch": details.get("servesLunch"),
                "serves_dinner": details.get("servesDinner"),
                "serves_vegetarian_food": details.get("servesVegetarianFood"),
                "dine_in": details.get("dineIn"),
                "delivery": details.get("delivery"),
                "takeout": details.get("takeout")
            }

            # Process reviews
            reviews = details.get("reviews", [])
            result["reviews"] = [
                {
                    "author_name": review.get("authorAttribution", {}).get("displayName"),
                    "author_url": review.get("authorAttribution", {}).get("uri"),
                    "profile_photo_url": review.get("authorAttribution", {}).get("photoUri"),
                    "rating": review.get("rating"),
                    "text": review.get("text", {}).get("text") if isinstance(review.get("text"), dict) else review.get("text"),
                    "publish_time": review.get("publishTime"),
                    "language": review.get("originalLanguage", "en")
                }
                for review in reviews
            ]

            # Process photos (get URLs for first 5)
            photos = details.get("photos", [])[:5]
            result["photos"] = [
                {
                    "photo_name": photo.get("name"),
                    "width": photo.get("widthPx"),
                    "height": photo.get("heightPx"),
                    "url": self.get_photo_url(photo.get("name"))
                }
                for photo in photos
            ]

            result["success"] = True
        else:
            result["errors"].append("Failed to fetch place details")

        logger.info(f"Collected Google data for {name}: success={result['success']}, reviews={len(result['reviews'])}")
        return result


# Singleton instance
_google_collector_instance = None


def get_google_collector() -> GooglePlacesCollector:
    """Get or create the Google Places collector singleton"""
    global _google_collector_instance
    if _google_collector_instance is None:
        _google_collector_instance = GooglePlacesCollector()
    return _google_collector_instance