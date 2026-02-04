"""
LLM Review Analyzer for Preference Extraction
Uses chain-of-thought prompting to extract structured insights from restaurant reviews
"""
import os
import json
from typing import Dict, List, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from loguru import logger


class LLMReviewAnalyzer:
    """
    Analyzes restaurant reviews using LLM to extract structured insights
    about cuisine, ambiance, service, and dining preferences.
    """

    def __init__(self):
        """Initialize the LLM analyzer with LiteLLM configuration"""
        self.api_key = os.getenv("LITELLM_API_KEY")
        self.base_url = os.getenv("LITELLM_BASE_URL", "https://api.ai.it.cornell.edu")
        self.model = os.getenv("LITELLM_MODEL", "openai.gpt-4o")

        if not self.api_key:
            raise ValueError("LITELLM_API_KEY environment variable is not set")

        # Initialize ChatOpenAI with Cornell LiteLLM proxy
        # API key read automatically from OPENAI_API_KEY env var
        self.llm = ChatOpenAI(
            model=self.model,
            openai_api_base=self.base_url,
            temperature=0.3,  # Lower temperature for more consistent analysis
            max_tokens=2000
        )

        # Chain-of-thought system prompt for review analysis
        # FIX: All braces {} in the JSON example below are doubled {{ }} to escape them
        self.system_prompt = """You are a restaurant analyst expert. Your task is to analyze restaurant reviews and extract structured insights about dining preferences.

IMPORTANT: You must ONLY extract information that is EXPLICITLY mentioned or STRONGLY implied in the reviews. Do NOT make assumptions or hallucinate details not supported by the text.

ANALYSIS PROCESS (Chain of Thought):
1. First, identify all EXPLICIT mentions of food items, dishes, flavors, and ingredients
2. Then, identify all EXPLICIT mentions of atmosphere, decor, noise level, and ambiance
3. Next, identify all EXPLICIT mentions of service quality, speed, and staff behavior
4. Identify any mentions of dining occasions (dates, family, groups, business)
5. Note any mentions of dietary accommodations or restrictions
6. Extract price perception from explicit price mentions or value comments
7. Finally, synthesize only the information that has supporting evidence

For each insight, consider the CONFIDENCE level:
- HIGH: Multiple reviews explicitly mention this
- MEDIUM: At least one review explicitly mentions this
- LOW: Implied but not directly stated
- DO NOT include insights with no supporting evidence

Return a JSON object with this exact structure:
{{
    "cuisine_style": "primary cuisine type (e.g., 'Italian', 'Mexican', 'Fusion') or null if unclear",
    "cuisine_subcategories": ["specific styles like 'Neapolitan Pizza', 'Northern Italian'] or empty array",
    "popular_dishes": ["dishes mentioned positively in reviews"] or empty array,
    "flavor_profile": {{
        "spice_level": "mild|medium|hot|very_hot or null if not mentioned",
        "dominant_flavors": ["flavors explicitly mentioned: savory, sweet, umami, tangy, etc."] or empty array,
        "sweetness": "not_sweet|slightly_sweet|sweet or null if not mentioned",
        "richness": "light|moderate|rich or null if not mentioned"
    }},
    "ambiance": {{
        "formality": "casual|smart_casual|formal or null if not mentioned",
        "noise_level": "quiet|moderate|loud|lively or null if not mentioned",
        "lighting": "dim|moderate|bright or null if not mentioned",
        "decor_style": "style description or null if not mentioned",
        "vibe": "overall vibe: romantic, trendy, cozy, upscale, etc. or null"
    }},
    "service_style": "fast|attentive|formal|casual or null if not mentioned",
    "dining_context": {{
        "romantic": true/false/null based on evidence,
        "family_friendly": true/false/null based on evidence,
        "good_for_groups": true/false/null based on evidence,
        "date_night": true/false/null based on evidence,
        "business_meeting": true/false/null based on evidence,
        "solo_dining": true/false/null based on evidence,
        "special_occasion": true/false/null based on evidence
    }},
    "portion_size": "small|moderate|generous or null if not mentioned",
    "best_for": ["meal occasions: lunch, dinner, brunch, late_night, drinks"] or empty array,
    "dietary_accommodations": ["vegetarian, vegan, gluten_free, etc. if mentioned"] or empty array,
    "standout_features": ["unique positive aspects mentioned in reviews"] or empty array,
    "price_perception": "great_value|fair|expensive|worth_it or null if not mentioned",
    "wait_time": "no_wait|short|moderate|long or null if not mentioned",
    "parking": "easy|street|valet|difficult or null if not mentioned",
    "overall_sentiment": "positive|mixed|negative based on review tone",
    "confidence": 0.0 to 1.0 overall confidence in the analysis,
    "evidence_summary": "Brief summary of key evidence from reviews supporting these insights"
}}"""

        # Create the prompt template
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("human", """Analyze the following restaurant reviews and extract structured dining insights.

Restaurant: {restaurant_name}
Location: {location}
Category: {category}
Price Level: {price_level}
Rating: {rating}

REVIEWS TO ANALYZE:
{reviews_text}

IMPORTANT INSTRUCTIONS:
1. Read through ALL reviews carefully before extracting insights
2. Only include information that has explicit evidence in the reviews
3. For each field, if there's no evidence, use null (for single values) or empty array (for lists)
4. Rate your overall confidence based on how much evidence supports your analysis
5. In evidence_summary, cite specific phrases or patterns from the reviews

Generate the JSON response following the specified structure. Ensure valid JSON syntax.""")
        ])

        # Create the chain
        self.chain = self.prompt_template | self.llm

    def analyze_reviews(
        self,
        reviews: List[Dict[str, Any]],
        restaurant_name: str = "Unknown",
        location: str = "Unknown",
        category: str = "Restaurant",
        price_level: Optional[str] = None,
        rating: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Analyze a list of reviews and extract structured insights
        """
        if not reviews:
            logger.warning(f"No reviews to analyze for {restaurant_name}")
            return self._get_empty_insights()

        # Format reviews for the prompt
        reviews_text = self._format_reviews(reviews)

        # --- LOGGING ADDED HERE ---
        logger.info(f"Analyzing {len(reviews)} reviews for {restaurant_name}")
        logger.debug(f"DEBUG: Reviews Text Payload for {restaurant_name}:\n{reviews_text}")
        # --------------------------

        try:
            # Invoke the LLM chain
            response = self.chain.invoke({
                "restaurant_name": restaurant_name,
                "location": location,
                "category": category,
                "price_level": price_level or "Not specified",
                "rating": str(rating) if rating else "Not specified",
                "reviews_text": reviews_text
            })

            # Extract content from the response
            content = response.content

            # Parse JSON from the response
            result = self._parse_json_response(content)

            # Validate and normalize the result
            result = self._normalize_insights(result)

            logger.info(f"Successfully analyzed reviews for {restaurant_name}, confidence: {result.get('confidence', 0)}")
            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            return self._get_empty_insights()
        except Exception as e:
            logger.error(f"Error analyzing reviews for {restaurant_name}: {e}")
            return self._get_empty_insights()

    def _format_reviews(self, reviews: List[Dict[str, Any]], max_chars: int = 6000) -> str:
        """
        Format reviews into a single text block for analysis
        """
        formatted_reviews = []
        total_chars = 0

        for i, review in enumerate(reviews, 1):
            text = review.get("text", "")
            rating = review.get("rating")

            if not text:
                continue

            # Format single review
            if rating:
                review_str = f"[Review {i}] (Rating: {rating}/5)\n{text}\n"
            else:
                review_str = f"[Review {i}]\n{text}\n"

            # Check character limit
            if total_chars + len(review_str) > max_chars:
                break

            formatted_reviews.append(review_str)
            total_chars += len(review_str)

        if not formatted_reviews:
            return "No review text available."

        return "\n".join(formatted_reviews)

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """
        Parse JSON from LLM response, handling markdown code blocks
        """
        # Try to extract JSON from code blocks
        if "```json" in content:
            json_start = content.find("```json") + 7
            json_end = content.find("```", json_start)
            json_str = content[json_start:json_end].strip()
        elif "```" in content:
            json_start = content.find("```") + 3
            json_end = content.find("```", json_start)
            json_str = content[json_start:json_end].strip()
        else:
            # Assume the entire content is JSON
            json_str = content.strip()

        return json.loads(json_str)

    def _normalize_insights(self, insights: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize and validate insight values
        """
        # Ensure all expected keys exist with proper defaults
        normalized = {
            "cuisine_style": insights.get("cuisine_style"),
            "cuisine_subcategories": insights.get("cuisine_subcategories", []) or [],
            "popular_dishes": insights.get("popular_dishes", []) or [],
            "flavor_profile": self._normalize_flavor_profile(insights.get("flavor_profile", {})),
            "ambiance": self._normalize_ambiance(insights.get("ambiance", {})),
            "service_style": insights.get("service_style"),
            "dining_context": self._normalize_dining_context(insights.get("dining_context", {})),
            "portion_size": insights.get("portion_size"),
            "best_for": insights.get("best_for", []) or [],
            "dietary_accommodations": insights.get("dietary_accommodations", []) or [],
            "standout_features": insights.get("standout_features", []) or [],
            "price_perception": insights.get("price_perception"),
            "wait_time": insights.get("wait_time"),
            "parking": insights.get("parking"),
            "overall_sentiment": insights.get("overall_sentiment", "mixed"),
            "confidence": min(max(insights.get("confidence", 0.5), 0.0), 1.0),
            "evidence_summary": insights.get("evidence_summary", "")
        }

        return normalized

    def _normalize_flavor_profile(self, profile: Optional[Dict]) -> Dict[str, Any]:
        """Normalize flavor profile values"""
        if not profile:
            return {
                "spice_level": None,
                "dominant_flavors": [],
                "sweetness": None,
                "richness": None
            }

        return {
            "spice_level": profile.get("spice_level"),
            "dominant_flavors": profile.get("dominant_flavors", []) or [],
            "sweetness": profile.get("sweetness"),
            "richness": profile.get("richness")
        }

    def _normalize_ambiance(self, ambiance: Optional[Dict]) -> Dict[str, Any]:
        """Normalize ambiance values"""
        if not ambiance:
            return {
                "formality": None,
                "noise_level": None,
                "lighting": None,
                "decor_style": None,
                "vibe": None
            }

        return {
            "formality": ambiance.get("formality"),
            "noise_level": ambiance.get("noise_level"),
            "lighting": ambiance.get("lighting"),
            "decor_style": ambiance.get("decor_style"),
            "vibe": ambiance.get("vibe")
        }

    def _normalize_dining_context(self, context: Optional[Dict]) -> Dict[str, Any]:
        """Normalize dining context values"""
        if not context:
            return {
                "romantic": None,
                "family_friendly": None,
                "good_for_groups": None,
                "date_night": None,
                "business_meeting": None,
                "solo_dining": None,
                "special_occasion": None
            }

        return {
            "romantic": context.get("romantic"),
            "family_friendly": context.get("family_friendly"),
            "good_for_groups": context.get("good_for_groups"),
            "date_night": context.get("date_night"),
            "business_meeting": context.get("business_meeting"),
            "solo_dining": context.get("solo_dining"),
            "special_occasion": context.get("special_occasion")
        }

    def _get_empty_insights(self) -> Dict[str, Any]:
        """Return empty insights structure when analysis fails"""
        return {
            "cuisine_style": None,
            "cuisine_subcategories": [],
            "popular_dishes": [],
            "flavor_profile": {
                "spice_level": None,
                "dominant_flavors": [],
                "sweetness": None,
                "richness": None
            },
            "ambiance": {
                "formality": None,
                "noise_level": None,
                "lighting": None,
                "decor_style": None,
                "vibe": None
            },
            "service_style": None,
            "dining_context": {
                "romantic": None,
                "family_friendly": None,
                "good_for_groups": None,
                "date_night": None,
                "business_meeting": None,
                "solo_dining": None,
                "special_occasion": None
            },
            "portion_size": None,
            "best_for": [],
            "dietary_accommodations": [],
            "standout_features": [],
            "price_perception": None,
            "wait_time": None,
            "parking": None,
            "overall_sentiment": None,
            "confidence": 0.0,
            "evidence_summary": "Analysis failed or no reviews available"
        }


# Singleton instance
_llm_analyzer_instance = None


def get_llm_analyzer() -> LLMReviewAnalyzer:
    """Get or create the LLM analyzer singleton"""
    global _llm_analyzer_instance
    if _llm_analyzer_instance is None:
        _llm_analyzer_instance = LLMReviewAnalyzer()
    return _llm_analyzer_instance