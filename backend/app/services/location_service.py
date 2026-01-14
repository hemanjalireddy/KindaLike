"""
Location Service for IP Geolocation
Detects user's location from their IP address
"""
import requests
from typing import Optional, Dict, Any


class LocationService:
    """Service for detecting user location from IP address"""

    def __init__(self):
        """Initialize location service"""
        # Using ip-api.com (free, no API key required for up to 45 requests/minute)
        self.base_url = "http://ip-api.com/json"

    def get_location_from_ip(self, ip_address: Optional[str] = None) -> Dict[str, Any]:
        """
        Get location information from IP address

        Args:
            ip_address: IP address to lookup (if None, uses the requester's IP)

        Returns:
            Dict with location info:
            {
                "city": "Ithaca",
                "region": "New York",
                "country": "United States",
                "lat": 42.4439,
                "lon": -76.5018,
                "zip": "14850",
                "timezone": "America/New_York",
                "formatted_location": "Ithaca, NY"
            }
        """
        # Build URL
        url = f"{self.base_url}/{ip_address}" if ip_address else self.base_url

        # Request specific fields for better performance
        params = {
            "fields": "status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone"
        }

        try:
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()

            # Check if request was successful
            if data.get("status") != "success":
                return {
                    "error": data.get("message", "Failed to get location"),
                    "city": "Ithaca",  # Default fallback
                    "region": "NY",
                    "formatted_location": "Ithaca, NY"
                }

            # Format the response
            return {
                "city": data.get("city", ""),
                "region": data.get("regionName", ""),
                "region_code": data.get("region", ""),
                "country": data.get("country", ""),
                "country_code": data.get("countryCode", ""),
                "zip": data.get("zip", ""),
                "lat": data.get("lat"),
                "lon": data.get("lon"),
                "timezone": data.get("timezone", ""),
                "formatted_location": f"{data.get('city', '')}, {data.get('region', '')}"
            }

        except requests.exceptions.RequestException as e:
            print(f"Error getting location from IP: {e}")
            # Return default location as fallback
            return {
                "error": str(e),
                "city": "Ithaca",
                "region": "NY",
                "formatted_location": "Ithaca, NY"
            }

    def extract_ip_from_request(self, request_headers: Dict[str, str]) -> Optional[str]:
        """
        Extract the real client IP from request headers
        Handles proxies and load balancers

        Args:
            request_headers: Dict of HTTP headers from the request

        Returns:
            IP address string or None
        """
        # Check common headers for the real IP
        ip_headers = [
            "X-Forwarded-For",
            "X-Real-IP",
            "CF-Connecting-IP",  # Cloudflare
            "True-Client-IP",    # Akamai
            "X-Client-IP"
        ]

        for header in ip_headers:
            ip = request_headers.get(header)
            if ip:
                # X-Forwarded-For can contain multiple IPs (client, proxy1, proxy2)
                # We want the first one (the client)
                if "," in ip:
                    ip = ip.split(",")[0].strip()
                return ip

        return None

    def get_coordinates(self, location: str) -> Optional[Dict[str, float]]:
        """
        Get coordinates for a location string (geocoding)
        Uses ip-api.com's geocoding endpoint (less accurate than dedicated services)

        Args:
            location: Location string (e.g., "Ithaca, NY")

        Returns:
            Dict with lat/lon or None if not found
        """
        # Note: For production, consider using a dedicated geocoding service
        # like Google Maps Geocoding API, Mapbox, or Nominatim (OpenStreetMap)

        # For now, return None and rely on Yelp's location parsing
        # Yelp API handles location strings very well
        return None


# Singleton instance
_location_service_instance = None


def get_location_service() -> LocationService:
    """Get or create the location service singleton"""
    global _location_service_instance
    if _location_service_instance is None:
        _location_service_instance = LocationService()
    return _location_service_instance
