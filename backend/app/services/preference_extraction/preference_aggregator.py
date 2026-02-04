"""
Preference Aggregator Service
Aggregates data from multiple sources (Yelp, Google, LLM, Questionnaire)
to build a cohesive preference profile.
"""
from typing import List, Dict, Any, Optional
from collections import Counter
from loguru import logger
import statistics

class PreferenceAggregator:
    def aggregate_preferences(
        self, 
        restaurant_data_list: List[Dict[str, Any]], 
        questionnaire_responses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Main entry point for aggregation.
        Combines restaurant metadata + user questionnaire answers.
        """
        restaurant_ids = [r['restaurant_id'] for r in restaurant_data_list]
        logger.info(f"Aggregating preferences from {len(restaurant_data_list)} restaurants")

        # 1. Aggregate fundamental attributes from Restaurant Data (Yelp/Google)
        base_preferences = {
            "price_sensitivity": self._aggregate_price(restaurant_data_list),
            "service_expectation": self._aggregate_rating(restaurant_data_list),
            "cuisine_preferences": self._aggregate_cuisines(restaurant_data_list),
            "atmosphere": self._aggregate_atmosphere(restaurant_data_list)
        }

        # 2. Integrate Questionnaire Responses
        # We overlay the explicit user answers on top of the derived data
        final_preferences = self._integrate_questionnaire_responses(
            base_preferences, 
            questionnaire_responses
        )

        return final_preferences

    def _aggregate_price(self, restaurant_data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregates price levels.
        Robustly handles Yelp's "$$" strings or numeric strings like "2".
        """
        price_levels = []

        for r in restaurant_data_list:
            # Check Yelp data
            yelp_price = r.get("yelp_data", {}).get("price")
            
            # Check Google data (sometimes google has price_level)
            google_price = r.get("google_data", {}).get("price_level")

            # Prioritize Yelp, fallback to Google
            raw_price = yelp_price if yelp_price else google_price

            if raw_price:
                # FIX: Convert string symbols/digits to actual integers
                normalized_price = self._normalize_price(raw_price)
                if normalized_price is not None:
                    price_levels.append(normalized_price)

        if not price_levels:
            return {"value": None, "confidence": 0.0, "source": "none"}

        # Calculate average
        avg_price = sum(price_levels) / len(price_levels)
        
        return {
            "value": round(avg_price, 1),
            "count": len(price_levels),
            "confidence": 0.8 if len(price_levels) >= 2 else 0.4,
            "source": "derived_from_restaurants"
        }

    def _normalize_price(self, value: Any) -> Optional[int]:
        """Helper to convert '$$' or '2' to integer 2."""
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str):
            # Handle Yelp "$$$" format
            if "$" in value:
                return len(value)
            # Handle numeric strings "2"
            if value.isdigit():
                return int(value)
        return None

    def _aggregate_rating(self, restaurant_data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregates ratings to determine quality/service expectations.
        """
        ratings = []

        for r in restaurant_data_list:
            # Yelp Rating
            y_rating = r.get("yelp_data", {}).get("rating")
            if y_rating is not None:
                try:
                    ratings.append(float(y_rating))
                except (ValueError, TypeError):
                    pass

            # Google Rating
            g_rating = r.get("google_data", {}).get("rating")
            if g_rating is not None:
                try:
                    ratings.append(float(g_rating))
                except (ValueError, TypeError):
                    pass

        if not ratings:
            return {"value": None, "confidence": 0.0}

        avg_rating = sum(ratings) / len(ratings)
        return {
            "value": round(avg_rating, 1),
            "confidence": 0.7 if len(ratings) >= 3 else 0.3,
            "source": "derived_from_restaurants"
        }

    def _aggregate_cuisines(self, restaurant_data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Counts cuisine tags to find the top favorites.
        """
        cuisine_counter = Counter()

        for r in restaurant_data_list:
            # Extract from Yelp categories
            categories = r.get("yelp_data", {}).get("categories", [])
            for cat in categories:
                # Yelp categories are often dicts: {'alias': 'italian', 'title': 'Italian'}
                title = cat.get("title") if isinstance(cat, dict) else cat
                if title:
                    cuisine_counter[title] += 1
            
            # Extract from LLM insights if available
            llm_cuisines = r.get("llm_insights", {}).get("cuisine_type")
            if llm_cuisines:
                if isinstance(llm_cuisines, list):
                    for c in llm_cuisines:
                        cuisine_counter[c] += 1
                elif isinstance(llm_cuisines, str):
                    cuisine_counter[llm_cuisines] += 1

        # Get top 3
        top_cuisines = [c[0] for c in cuisine_counter.most_common(3)]
        
        return {
            "top_cuisines": top_cuisines,
            "all_counts": dict(cuisine_counter),
            "source": "derived_from_restaurants"
        }

    def _aggregate_atmosphere(self, restaurant_data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregates atmosphere keywords from LLM insights.
        """
        vibes = Counter()
        
        for r in restaurant_data_list:
            # Check LLM insights for "atmosphere" or "vibe"
            insights = r.get("llm_insights", {})
            vibe_list = insights.get("atmosphere") or insights.get("vibe", [])
            
            if isinstance(vibe_list, list):
                for v in vibe_list:
                    vibes[v.lower()] += 1
            elif isinstance(vibe_list, str):
                vibes[vibe_list.lower()] += 1

        return {
            "top_vibes": [v[0] for v in vibes.most_common(5)],
            "source": "derived_from_restaurants"
        }

    def _integrate_questionnaire_responses(
        self, 
        base_prefs: Dict[str, Any], 
        responses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Merges explicit questionnaire answers into the preference profile.
        Explicit answers (high confidence) override or augment derived data.
        """
        final_profile = base_prefs.copy()
        
        for response in responses:
            # In a real app, you would map question_id to specific preference fields.
            # Here, we generalize for the example.
            
            # Example structure of response: {'question_id': 'q1', 'answer_value': 4}
            # You might interpret 'q_price' updates 'price_sensitivity'
            pass
            
        # For now, we return the base preferences + the raw responses for the scorer to handle
        final_profile["explicit_responses"] = responses
        return final_profile


def get_preference_aggregator():
    return PreferenceAggregator()