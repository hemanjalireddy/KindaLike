"""
Preference Scorer Service
Calculates confidence scores and weights for user preferences
"""
import json
from typing import Dict, List, Any, Optional
from loguru import logger


class PreferenceScorer:
    """
    Calculates confidence scores and importance weights for preferences.
    Applies scoring algorithms based on data consistency and completeness.
    """

    def __init__(self):
        """Initialize the preference scorer"""
        # Category weights for recommendations
        self.category_weights = {
            "cuisine": 0.30,      # Cuisine type is most important
            "price": 0.15,        # Price range
            "flavor": 0.12,       # Flavor preferences
            "ambiance": 0.12,     # Atmosphere preferences
            "dietary": 0.10,      # Dietary requirements
            "location": 0.08,     # Location preferences
            "quality": 0.08,      # Quality expectations
            "service": 0.05       # Service style
        }

        # Scoring parameters
        self.base_confidence = 0.50
        self.consistency_bonus = {
            "high": 0.20,
            "medium": 0.10,
            "exploratory": 0.00,
            "unknown": -0.10
        }
        self.data_completeness_bonus = 0.15
        self.user_confirmation_bonus = 0.10
        self.max_initial_confidence = 0.85

    def calculate_scores(
        self,
        aggregated_prefs: Dict[str, Any],
        data_completeness: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Calculate final scores for all preferences

        Args:
            aggregated_prefs: Aggregated preference data from PreferenceAggregator
            data_completeness: Overall data completeness score (0-1)

        Returns:
            List of preference dicts ready for database storage
        """
        preferences = []

        # Process cuisine preferences
        cuisine_prefs = self._score_cuisine_preferences(
            aggregated_prefs.get("cuisine", {}),
            data_completeness
        )
        preferences.extend(cuisine_prefs)

        # Process price preferences
        price_prefs = self._score_price_preferences(
            aggregated_prefs.get("price", {}),
            data_completeness
        )
        preferences.extend(price_prefs)

        # Process flavor preferences
        flavor_prefs = self._score_flavor_preferences(
            aggregated_prefs.get("flavor", {}),
            data_completeness
        )
        preferences.extend(flavor_prefs)

        # Process ambiance preferences
        ambiance_prefs = self._score_ambiance_preferences(
            aggregated_prefs.get("ambiance", {}),
            data_completeness
        )
        preferences.extend(ambiance_prefs)

        # Process dietary preferences
        dietary_prefs = self._score_dietary_preferences(
            aggregated_prefs.get("dietary", {}),
            data_completeness
        )
        preferences.extend(dietary_prefs)

        # Process dining context preferences
        context_prefs = self._score_dining_context_preferences(
            aggregated_prefs.get("dining_context", {}),
            data_completeness
        )
        preferences.extend(context_prefs)

        # Process service preferences
        service_prefs = self._score_service_preferences(
            aggregated_prefs.get("service", {}),
            data_completeness
        )
        preferences.extend(service_prefs)

        # Process meal time preferences
        meal_prefs = self._score_meal_preferences(
            aggregated_prefs.get("best_for", {}),
            data_completeness
        )
        preferences.extend(meal_prefs)

        # Process favorite dishes if present
        if aggregated_prefs.get("favorite_dishes"):
            dish_prefs = self._score_favorite_dishes(
                aggregated_prefs["favorite_dishes"]
            )
            preferences.extend(dish_prefs)

        logger.info(f"Scored {len(preferences)} preferences")
        return preferences

    def _calculate_confidence(
        self,
        base_confidence: float,
        consistency: str,
        data_completeness: float,
        user_confirmed: bool = False
    ) -> float:
        """
        Calculate final confidence score

        Args:
            base_confidence: Starting confidence from aggregation
            consistency: Consistency level ('high', 'medium', 'exploratory', 'unknown')
            data_completeness: Data completeness score (0-1)
            user_confirmed: Whether user confirmed this in questionnaire

        Returns:
            Final confidence score (0-1)
        """
        score = base_confidence

        # Apply consistency bonus
        score += self.consistency_bonus.get(consistency, 0)

        # Apply data completeness bonus (proportional)
        score += self.data_completeness_bonus * data_completeness

        # Apply user confirmation bonus
        if user_confirmed:
            score += self.user_confirmation_bonus

        # Clamp to valid range
        return min(max(score, 0.0), self.max_initial_confidence)

    def _score_cuisine_preferences(
        self,
        cuisine_data: Dict[str, Any],
        data_completeness: float
    ) -> List[Dict[str, Any]]:
        """Score cuisine-related preferences"""
        preferences = []

        if not cuisine_data:
            return preferences

        primary_cuisines = cuisine_data.get("primary_cuisines", [])
        consistency = cuisine_data.get("consistency", "unknown")
        base_conf = cuisine_data.get("confidence_score", 0.50)
        restaurant_ids = cuisine_data.get("source_restaurants", [])

        # Create preference for each primary cuisine
        for i, cuisine in enumerate(primary_cuisines[:3]):
            # First cuisine gets full weight, others get reduced
            weight_multiplier = 1.0 if i == 0 else 0.5 if i == 1 else 0.3

            pref = {
                "category": "cuisine",
                "subcategory": "primary" if i == 0 else "secondary",
                "value_text": cuisine,
                "value_json": {"rank": i + 1, "cuisine": cuisine},
                "confidence_score": self._calculate_confidence(
                    base_conf, consistency, data_completeness
                ),
                "weight": self.category_weights["cuisine"] * weight_multiplier,
                "source": "onboarding",
                "derived_from_restaurants": restaurant_ids
            }
            preferences.append(pref)

        # Add subcategories as exploration preferences
        for subcat in cuisine_data.get("subcategories", [])[:3]:
            pref = {
                "category": "cuisine",
                "subcategory": "style",
                "value_text": subcat,
                "confidence_score": self._calculate_confidence(
                    base_conf * 0.8, consistency, data_completeness
                ),
                "weight": self.category_weights["cuisine"] * 0.2,
                "source": "onboarding",
                "derived_from_restaurants": restaurant_ids
            }
            preferences.append(pref)

        return preferences

    def _score_price_preferences(
        self,
        price_data: Dict[str, Any],
        data_completeness: float
    ) -> List[Dict[str, Any]]:
        """Score price-related preferences"""
        preferences = []

        if not price_data:
            return preferences

        consistency = price_data.get("consistency", "unknown")
        base_conf = price_data.get("confidence_score", 0.50)
        restaurant_ids = price_data.get("source_restaurants", [])

        # Main price preference
        avg_level = price_data.get("average_level", 2)
        user_level = price_data.get("user_preferred_level")

        # Use user preference if available, otherwise use average
        final_level = user_level if user_level else avg_level
        user_confirmed = user_level is not None

        pref = {
            "category": "price",
            "subcategory": "range",
            "value_numeric": final_level,
            "value_text": "$" * round(final_level),
            "value_json": {
                "level": final_level,
                "range": price_data.get("range", []),
                "flexible": len(price_data.get("range", [])) > 1
            },
            "confidence_score": self._calculate_confidence(
                base_conf, consistency, data_completeness, user_confirmed
            ),
            "weight": self.category_weights["price"],
            "source": "onboarding",
            "derived_from_restaurants": restaurant_ids
        }
        preferences.append(pref)

        return preferences

    def _score_flavor_preferences(
        self,
        flavor_data: Dict[str, Any],
        data_completeness: float
    ) -> List[Dict[str, Any]]:
        """Score flavor-related preferences"""
        preferences = []

        if not flavor_data:
            return preferences

        consistency = flavor_data.get("consistency", "unknown")
        base_conf = flavor_data.get("confidence_score", 0.50)
        restaurant_ids = flavor_data.get("source_restaurants", [])

        # Spice level preference
        spice_level = flavor_data.get("preferred_spice_level")
        if spice_level:
            pref = {
                "category": "flavor",
                "subcategory": "spice_level",
                "value_text": spice_level,
                "confidence_score": self._calculate_confidence(
                    base_conf, consistency, data_completeness
                ),
                "weight": self.category_weights["flavor"] * 0.4,
                "source": "onboarding",
                "derived_from_restaurants": restaurant_ids
            }
            preferences.append(pref)

        # Dominant flavors
        dominant_flavors = flavor_data.get("dominant_flavors", [])
        if dominant_flavors:
            pref = {
                "category": "flavor",
                "subcategory": "dominant",
                "value_json": {"flavors": dominant_flavors},
                "confidence_score": self._calculate_confidence(
                    base_conf * 0.8, consistency, data_completeness
                ),
                "weight": self.category_weights["flavor"] * 0.4,
                "source": "onboarding",
                "derived_from_restaurants": restaurant_ids
            }
            preferences.append(pref)

        # Richness preference
        richness = flavor_data.get("preferred_richness")
        if richness:
            pref = {
                "category": "flavor",
                "subcategory": "richness",
                "value_text": richness,
                "confidence_score": self._calculate_confidence(
                    base_conf * 0.7, consistency, data_completeness
                ),
                "weight": self.category_weights["flavor"] * 0.2,
                "source": "onboarding",
                "derived_from_restaurants": restaurant_ids
            }
            preferences.append(pref)

        return preferences

    def _score_ambiance_preferences(
        self,
        ambiance_data: Dict[str, Any],
        data_completeness: float
    ) -> List[Dict[str, Any]]:
        """Score ambiance-related preferences"""
        preferences = []

        if not ambiance_data:
            return preferences

        consistency = ambiance_data.get("consistency", "unknown")
        base_conf = ambiance_data.get("confidence_score", 0.50)
        restaurant_ids = ambiance_data.get("source_restaurants", [])

        # Formality preference
        formality = ambiance_data.get("preferred_formality")
        if formality:
            pref = {
                "category": "ambiance",
                "subcategory": "formality",
                "value_text": formality,
                "confidence_score": self._calculate_confidence(
                    base_conf, consistency, data_completeness
                ),
                "weight": self.category_weights["ambiance"] * 0.4,
                "source": "onboarding",
                "derived_from_restaurants": restaurant_ids
            }
            preferences.append(pref)

        # Vibe preference (user confirmed or derived)
        vibe = ambiance_data.get("user_preferred_vibe") or ambiance_data.get("preferred_vibe")
        user_confirmed = ambiance_data.get("user_preferred_vibe") is not None
        if vibe:
            pref = {
                "category": "ambiance",
                "subcategory": "vibe",
                "value_text": vibe,
                "value_json": {"all_vibes": ambiance_data.get("all_vibes", [])},
                "confidence_score": self._calculate_confidence(
                    base_conf, consistency, data_completeness, user_confirmed
                ),
                "weight": self.category_weights["ambiance"] * 0.4,
                "source": "onboarding",
                "derived_from_restaurants": restaurant_ids
            }
            preferences.append(pref)

        # Noise level preference
        noise_level = ambiance_data.get("preferred_noise_level")
        if noise_level:
            pref = {
                "category": "ambiance",
                "subcategory": "noise_level",
                "value_text": noise_level,
                "confidence_score": self._calculate_confidence(
                    base_conf * 0.7, consistency, data_completeness
                ),
                "weight": self.category_weights["ambiance"] * 0.2,
                "source": "onboarding",
                "derived_from_restaurants": restaurant_ids
            }
            preferences.append(pref)

        return preferences

    def _score_dietary_preferences(
        self,
        dietary_data: Dict[str, Any],
        data_completeness: float
    ) -> List[Dict[str, Any]]:
        """Score dietary-related preferences"""
        preferences = []

        if not dietary_data:
            return preferences

        accommodations = dietary_data.get("accommodations", [])
        if not accommodations or accommodations == ["none"]:
            # No dietary restrictions
            pref = {
                "category": "dietary",
                "subcategory": "restrictions",
                "value_text": "none",
                "value_json": {"restrictions": []},
                "confidence_score": 0.70,
                "weight": self.category_weights["dietary"],
                "source": "onboarding",
                "derived_from_restaurants": dietary_data.get("source_restaurants", [])
            }
            preferences.append(pref)
        else:
            # Has dietary requirements
            pref = {
                "category": "dietary",
                "subcategory": "restrictions",
                "value_json": {"restrictions": accommodations},
                "confidence_score": self._calculate_confidence(
                    dietary_data.get("confidence_score", 0.60),
                    dietary_data.get("consistency", "medium"),
                    data_completeness,
                    True  # Dietary is usually confirmed
                ),
                "weight": self.category_weights["dietary"],
                "source": "onboarding",
                "derived_from_restaurants": dietary_data.get("source_restaurants", [])
            }
            preferences.append(pref)

        return preferences

    def _score_dining_context_preferences(
        self,
        context_data: Dict[str, Any],
        data_completeness: float
    ) -> List[Dict[str, Any]]:
        """Score dining context preferences"""
        preferences = []

        if not context_data:
            return preferences

        context_prefs = context_data.get("preferences", {})
        restaurant_ids = context_data.get("source_restaurants", [])
        base_conf = context_data.get("confidence_score", 0.60)

        # Create preference for true contexts
        true_contexts = [k for k, v in context_prefs.items() if v is True]

        if true_contexts:
            pref = {
                "category": "occasion",
                "subcategory": "preferred",
                "value_json": {"contexts": true_contexts},
                "confidence_score": base_conf,
                "weight": 0.08,  # Occasion weight
                "source": "onboarding",
                "derived_from_restaurants": restaurant_ids
            }
            preferences.append(pref)

        return preferences

    def _score_service_preferences(
        self,
        service_data: Dict[str, Any],
        data_completeness: float
    ) -> List[Dict[str, Any]]:
        """Score service-related preferences"""
        preferences = []

        if not service_data:
            return preferences

        preferred_style = service_data.get("preferred_style")
        if preferred_style:
            pref = {
                "category": "service",
                "subcategory": "style",
                "value_text": preferred_style,
                "confidence_score": self._calculate_confidence(
                    service_data.get("confidence_score", 0.50),
                    service_data.get("consistency", "medium"),
                    data_completeness
                ),
                "weight": self.category_weights["service"],
                "source": "onboarding",
                "derived_from_restaurants": service_data.get("source_restaurants", [])
            }
            preferences.append(pref)

        return preferences

    def _score_meal_preferences(
        self,
        meal_data: Dict[str, Any],
        data_completeness: float
    ) -> List[Dict[str, Any]]:
        """Score meal time preferences"""
        preferences = []

        if not meal_data:
            return preferences

        preferred_meals = meal_data.get("preferred_meals", [])
        if preferred_meals:
            pref = {
                "category": "occasion",
                "subcategory": "meal_time",
                "value_json": {"meals": preferred_meals},
                "confidence_score": meal_data.get("confidence_score", 0.60),
                "weight": 0.05,
                "source": "onboarding",
                "derived_from_restaurants": meal_data.get("source_restaurants", [])
            }
            preferences.append(pref)

        return preferences

    def _score_favorite_dishes(
        self,
        dishes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Score favorite dishes from questionnaire"""
        preferences = []

        for dish_info in dishes:
            pref = {
                "category": "dish",
                "subcategory": "favorite",
                "value_text": dish_info.get("dish"),
                "value_json": {
                    "dish": dish_info.get("dish"),
                    "restaurant_id": dish_info.get("restaurant_id")
                },
                "confidence_score": 0.90,  # User explicitly stated
                "weight": 0.05,  # Dish preferences are specific signals
                "source": "questionnaire",
                "derived_from_restaurants": [dish_info.get("restaurant_id")] if dish_info.get("restaurant_id") else []
            }
            preferences.append(pref)

        return preferences


# Singleton instance
_scorer_instance = None


def get_preference_scorer() -> PreferenceScorer:
    """Get or create the preference scorer singleton"""
    global _scorer_instance
    if _scorer_instance is None:
        _scorer_instance = PreferenceScorer()
    return _scorer_instance
