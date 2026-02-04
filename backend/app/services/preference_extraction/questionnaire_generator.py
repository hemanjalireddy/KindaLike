"""
Questionnaire Generator Service
Generates targeted follow-up questions based on data gaps
"""
from typing import Dict, List, Any, Optional
from loguru import logger


class QuestionnaireGenerator:
    """
    Generates targeted questionnaire questions based on what data
    is missing or unclear from API and LLM analysis.
    """

    def __init__(self):
        """Initialize the questionnaire generator"""
        # Question templates organized by category
        self.question_templates = {
            "dish": {
                "favorite_dish": {
                    "question_text": "What's your favorite dish at {restaurant_name}?",
                    "question_type": "text",
                    "required": True,
                    "always_ask": True
                },
                "dish_style": {
                    "question_text": "What type of dishes do you usually order at {restaurant_name}?",
                    "question_type": "multi_choice",
                    "options": [
                        {"value": "appetizers", "label": "Appetizers / Small plates"},
                        {"value": "mains", "label": "Main courses"},
                        {"value": "sharing", "label": "Sharing plates"},
                        {"value": "tasting", "label": "Tasting menus"},
                        {"value": "desserts", "label": "Desserts"}
                    ],
                    "required": False
                }
            },
            "flavor": {
                "spice_preference": {
                    "question_text": "How spicy do you typically like your food at {restaurant_name}?",
                    "question_type": "single_choice",
                    "options": [
                        {"value": "no_spice", "label": "No spice"},
                        {"value": "mild", "label": "Mild"},
                        {"value": "medium", "label": "Medium"},
                        {"value": "hot", "label": "Hot"},
                        {"value": "very_hot", "label": "Very hot"}
                    ],
                    "required": False,
                    "ask_when_missing": "spice_level"
                },
                "flavor_preferences": {
                    "question_text": "What flavors do you enjoy most when dining at {restaurant_name}?",
                    "question_type": "multi_choice",
                    "options": [
                        {"value": "savory", "label": "Savory / Umami"},
                        {"value": "sweet", "label": "Sweet"},
                        {"value": "tangy", "label": "Tangy / Sour"},
                        {"value": "rich", "label": "Rich / Creamy"},
                        {"value": "fresh", "label": "Fresh / Light"}
                    ],
                    "required": False,
                    "ask_when_missing": "dominant_flavors"
                }
            },
            "ambiance": {
                "ambiance_preference": {
                    "question_text": "How would you describe the atmosphere at {restaurant_name}?",
                    "question_type": "single_choice",
                    "options": [
                        {"value": "casual", "label": "Casual and relaxed"},
                        {"value": "trendy", "label": "Trendy and modern"},
                        {"value": "cozy", "label": "Cozy and intimate"},
                        {"value": "upscale", "label": "Upscale and elegant"},
                        {"value": "lively", "label": "Lively and energetic"}
                    ],
                    "required": False,
                    "ask_when_missing": "vibe"
                },
                "noise_preference": {
                    "question_text": "What's the noise level like when you visit {restaurant_name}?",
                    "question_type": "single_choice",
                    "options": [
                        {"value": "quiet", "label": "Quiet - easy to have conversation"},
                        {"value": "moderate", "label": "Moderate background noise"},
                        {"value": "lively", "label": "Lively and bustling"},
                        {"value": "loud", "label": "Loud and energetic"}
                    ],
                    "required": False,
                    "ask_when_missing": "noise_level"
                }
            },
            "occasion": {
                "visit_occasion": {
                    "question_text": "When do you usually visit {restaurant_name}?",
                    "question_type": "multi_choice",
                    "options": [
                        {"value": "casual_meal", "label": "Casual weekday meal"},
                        {"value": "date_night", "label": "Date night"},
                        {"value": "family", "label": "Family dinner"},
                        {"value": "friends", "label": "With friends"},
                        {"value": "special_occasion", "label": "Special occasions"},
                        {"value": "business", "label": "Business meals"}
                    ],
                    "required": True,
                    "always_ask": True
                },
                "meal_time": {
                    "question_text": "What meal do you typically have at {restaurant_name}?",
                    "question_type": "multi_choice",
                    "options": [
                        {"value": "breakfast", "label": "Breakfast"},
                        {"value": "brunch", "label": "Brunch"},
                        {"value": "lunch", "label": "Lunch"},
                        {"value": "dinner", "label": "Dinner"},
                        {"value": "late_night", "label": "Late night"}
                    ],
                    "required": False,
                    "ask_when_missing": "best_for"
                }
            },
            "dietary": {
                "dietary_options": {
                    "question_text": "Do you order any special dietary options at {restaurant_name}?",
                    "question_type": "multi_choice",
                    "options": [
                        {"value": "none", "label": "No specific dietary needs"},
                        {"value": "vegetarian", "label": "Vegetarian"},
                        {"value": "vegan", "label": "Vegan"},
                        {"value": "gluten_free", "label": "Gluten-free"},
                        {"value": "dairy_free", "label": "Dairy-free"},
                        {"value": "halal", "label": "Halal"},
                        {"value": "kosher", "label": "Kosher"}
                    ],
                    "required": False,
                    "ask_when_missing": "dietary_accommodations"
                }
            },
            "general": {
                "overall_experience": {
                    "question_text": "What do you love most about {restaurant_name}?",
                    "question_type": "multi_choice",
                    "options": [
                        {"value": "food_quality", "label": "Food quality"},
                        {"value": "service", "label": "Service"},
                        {"value": "ambiance", "label": "Ambiance"},
                        {"value": "value", "label": "Value for money"},
                        {"value": "location", "label": "Location / Convenience"},
                        {"value": "unique_dishes", "label": "Unique dishes"}
                    ],
                    "required": True,
                    "always_ask": True
                }
            }
        }

    def generate_questions(
        self,
        restaurant_data: List[Dict[str, Any]],
        max_questions_per_restaurant: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Generate targeted questions based on data gaps

        Args:
            restaurant_data: List of collected data for each restaurant
            max_questions_per_restaurant: Maximum questions per restaurant

        Returns:
            List of question dicts ready for the questionnaire
        """
        all_questions = []
        question_counter = 0

        for rest_data in restaurant_data:
            restaurant_id = rest_data.get("restaurant_id")
            restaurant_name = rest_data.get("restaurant_name", "this restaurant")
            llm_insights = rest_data.get("llm_insights", {}) or {}

            restaurant_questions = []

            # Identify data gaps
            data_gaps = self._identify_data_gaps(llm_insights)

            # Always ask certain questions
            for category, templates in self.question_templates.items():
                for q_id, template in templates.items():
                    if template.get("always_ask"):
                        question = self._create_question(
                            question_id=f"q_{question_counter}_{q_id}",
                            template=template,
                            restaurant_id=restaurant_id,
                            restaurant_name=restaurant_name,
                            category=category
                        )
                        restaurant_questions.append(question)
                        question_counter += 1

            # Ask questions for missing data
            for category, templates in self.question_templates.items():
                for q_id, template in templates.items():
                    if template.get("always_ask"):
                        continue  # Already added

                    ask_when = template.get("ask_when_missing")
                    if ask_when and ask_when in data_gaps:
                        question = self._create_question(
                            question_id=f"q_{question_counter}_{q_id}",
                            template=template,
                            restaurant_id=restaurant_id,
                            restaurant_name=restaurant_name,
                            category=category
                        )
                        restaurant_questions.append(question)
                        question_counter += 1

            # Limit questions per restaurant
            all_questions.extend(restaurant_questions[:max_questions_per_restaurant])

        logger.info(f"Generated {len(all_questions)} questionnaire questions")
        return all_questions

    def _identify_data_gaps(self, llm_insights: Dict[str, Any]) -> set:
        """
        Identify what data is missing or has low confidence

        Args:
            llm_insights: LLM analysis results

        Returns:
            Set of missing data field names
        """
        gaps = set()

        if not llm_insights:
            # Everything is missing
            return {
                "spice_level", "dominant_flavors", "vibe", "noise_level",
                "best_for", "dietary_accommodations"
            }

        # Check flavor profile (handle None explicitly)
        flavor = llm_insights.get("flavor_profile") or {}
        if not flavor.get("spice_level"):
            gaps.add("spice_level")
        if not flavor.get("dominant_flavors"):
            gaps.add("dominant_flavors")

        # Check ambiance (handle None explicitly)
        ambiance = llm_insights.get("ambiance") or {}
        if not ambiance.get("vibe"):
            gaps.add("vibe")
        if not ambiance.get("noise_level"):
            gaps.add("noise_level")

        # Check other fields
        if not llm_insights.get("best_for"):
            gaps.add("best_for")
        if not llm_insights.get("dietary_accommodations"):
            gaps.add("dietary_accommodations")

        # Check dining context (handle None explicitly)
        context = llm_insights.get("dining_context") or {}
        context_known = any(v is not None for v in context.values()) if context else False
        if not context_known:
            gaps.add("dining_context")

        return gaps

    def _create_question(
        self,
        question_id: str,
        template: Dict[str, Any],
        restaurant_id: int,
        restaurant_name: str,
        category: str
    ) -> Dict[str, Any]:
        """
        Create a question dict from a template

        Args:
            question_id: Unique question ID
            template: Question template
            restaurant_id: Restaurant ID
            restaurant_name: Restaurant name for formatting
            category: Question category

        Returns:
            Question dict
        """
        question = {
            "question_id": question_id,
            "restaurant_id": restaurant_id,
            "restaurant_name": restaurant_name,
            "question_text": template["question_text"].format(restaurant_name=restaurant_name),
            "question_type": template["question_type"],
            "category": category,
            "required": template.get("required", False)
        }

        if "options" in template:
            question["options"] = template["options"]

        return question

    def generate_global_questions(self) -> List[Dict[str, Any]]:
        """
        Generate questions that apply across all restaurants

        Returns:
            List of global question dicts
        """
        return [
            {
                "question_id": "global_price",
                "restaurant_id": None,
                "restaurant_name": None,
                "question_text": "In general, what price range do you prefer when dining out?",
                "question_type": "single_choice",
                "category": "price",
                "required": True,
                "options": [
                    {"value": "1", "label": "$ - Budget friendly"},
                    {"value": "2", "label": "$$ - Moderate"},
                    {"value": "3", "label": "$$$ - Upscale"},
                    {"value": "4", "label": "$$$$ - Fine dining"}
                ]
            },
            {
                "question_id": "global_distance",
                "restaurant_id": None,
                "restaurant_name": None,
                "question_text": "How far are you typically willing to travel for a good restaurant?",
                "question_type": "single_choice",
                "category": "location",
                "required": False,
                "options": [
                    {"value": "nearby", "label": "Nearby (< 10 min)"},
                    {"value": "moderate", "label": "Moderate (10-20 min)"},
                    {"value": "willing_to_travel", "label": "Will travel (20-30 min)"},
                    {"value": "anywhere", "label": "Anywhere for great food"}
                ]
            },
            {
                "question_id": "global_discovery",
                "restaurant_id": None,
                "restaurant_name": None,
                "question_text": "Do you prefer trying new restaurants or sticking to favorites?",
                "question_type": "single_choice",
                "category": "behavior",
                "required": False,
                "options": [
                    {"value": "adventurous", "label": "Love trying new places"},
                    {"value": "mix", "label": "Mix of new and familiar"},
                    {"value": "favorites", "label": "Prefer my favorites"}
                ]
            }
        ]


# Singleton instance
_questionnaire_generator_instance = None


def get_questionnaire_generator() -> QuestionnaireGenerator:
    """Get or create the questionnaire generator singleton"""
    global _questionnaire_generator_instance
    if _questionnaire_generator_instance is None:
        _questionnaire_generator_instance = QuestionnaireGenerator()
    return _questionnaire_generator_instance
