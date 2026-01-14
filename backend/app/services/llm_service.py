"""
LLM Service for Restaurant Category Generation
Ports the hierarchical category generation logic from the Jupyter notebook
"""
import os
import json
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate


class LLMService:
    """Service for generating restaurant categories using LLM"""

    def __init__(self):
        """Initialize the LLM service with LiteLLM configuration"""
        self.api_key = os.getenv("LITELLM_API_KEY")
        self.base_url = os.getenv("LITELLM_BASE_URL", "https://api.ai.it.cornell.edu")
        self.model = os.getenv("LITELLM_MODEL", "openai.gpt-4o")

        if not self.api_key:
            raise ValueError("LITELLM_API_KEY environment variable is not set")

        # Initialize ChatOpenAI with LiteLLM configuration
        self.llm = ChatOpenAI(
            model=self.model,
            api_key=self.api_key,
            base_url=self.base_url,
            temperature=0.7,
            max_tokens=500
        )

        # System prompt for category generation
        self.system_prompt = """You are a restaurant recommendation expert.
Your task is to analyze user queries and generate structured search parameters for finding restaurants.

When a user asks for restaurant recommendations, break down their request into:
1. Hierarchical categories (from general to specific)
2. Primary search categories for Yelp API
3. Key attributes (cuisine, price, occasion, ambiance, special features)

Be flexible and creative in interpretation. Consider implicit meanings:
- "date night" → romantic, upscale, intimate atmosphere
- "quick bite" → casual, fast, affordable
- "celebration" → upscale, special occasion, lively
- "healthy" → fresh, organic, vegetarian/vegan options

Return a JSON object with this exact structure:
{{
    "hierarchical_categories": ["General Category", "Specific Category", "Very Specific"],
    "primary_categories": ["yelp_category1", "yelp_category2"],
    "attributes": {{
        "cuisine_type": "string or null",
        "price_level": "1-4 or null",
        "occasion": "string or null",
        "ambiance_keywords": ["keyword1", "keyword2"],
        "special_features": ["feature1", "feature2"]
    }},
    "reasoning": "Brief explanation of your interpretation"
}}"""

        # Create the prompt template
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("human", """Analyze this restaurant request and generate search parameters:

User Query: {query}

User Preferences (if available):
- Cuisine: {cuisine_type}
- Price Range: {price_range}
- Dining Style: {dining_style}
- Dietary Restrictions: {dietary_restrictions}
- Atmosphere: {atmosphere}

Generate the JSON response following the specified structure.""")
        ])

        # Create the chain
        self.chain = self.prompt_template | self.llm

    def generate_categories(
        self,
        query: str,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate hierarchical restaurant categories from user query

        Args:
            query: User's restaurant request (e.g., "I want Italian food for a date night")
            user_preferences: Optional dict with user's saved preferences
                {
                    "cuisine_type": "Italian",
                    "price_range": "$$",
                    "dining_style": "Fine Dining",
                    "dietary_restrictions": "None",
                    "atmosphere": "Romantic"
                }

        Returns:
            Dict containing hierarchical categories and search parameters
        """
        # Prepare user preferences with defaults
        prefs = user_preferences or {}
        cuisine_type = prefs.get("cuisine_type", "Not specified")
        price_range = prefs.get("price_range", "Not specified")
        dining_style = prefs.get("dining_style", "Not specified")
        dietary_restrictions = prefs.get("dietary_restrictions", "Not specified")
        atmosphere = prefs.get("atmosphere", "Not specified")

        try:
            # Invoke the LLM chain
            response = self.chain.invoke({
                "query": query,
                "cuisine_type": cuisine_type,
                "price_range": price_range,
                "dining_style": dining_style,
                "dietary_restrictions": dietary_restrictions,
                "atmosphere": atmosphere
            })

            # Extract content from the response
            content = response.content

            # Parse JSON from the response
            # The LLM might wrap JSON in markdown code blocks
            if "```json" in content:
                # Extract JSON from code block
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                json_str = content[json_start:json_end].strip()
            elif "```" in content:
                # Generic code block
                json_start = content.find("```") + 3
                json_end = content.find("```", json_start)
                json_str = content[json_start:json_end].strip()
            else:
                # Assume the entire content is JSON
                json_str = content.strip()

            result = json.loads(json_str)

            # Validate the structure
            required_keys = ["hierarchical_categories", "primary_categories", "attributes"]
            if not all(key in result for key in required_keys):
                raise ValueError(f"LLM response missing required keys. Got: {result.keys()}")

            return result

        except json.JSONDecodeError as e:
            # Fallback if JSON parsing fails
            print(f"Failed to parse LLM response as JSON: {e}")
            print(f"Raw response: {content}")
            return self._get_fallback_categories(query, prefs)
        except Exception as e:
            print(f"Error generating categories: {e}")
            return self._get_fallback_categories(query, prefs)

    def _get_fallback_categories(
        self,
        query: str,
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Fallback category generation if LLM fails
        Uses simple keyword matching and user preferences
        """
        cuisine = preferences.get("cuisine_type", "restaurants")
        price = preferences.get("price_range", "$$")

        # Simple price mapping
        price_map = {
            "$": 1,
            "$$": 2,
            "$$$": 3,
            "$$$$": 4
        }

        return {
            "hierarchical_categories": [
                "Food & Dining",
                "Restaurants",
                cuisine if cuisine != "Not specified" else "All Cuisines"
            ],
            "primary_categories": ["restaurants"],
            "attributes": {
                "cuisine_type": cuisine if cuisine != "Not specified" else None,
                "price_level": price_map.get(price, 2),
                "occasion": "casual",
                "ambiance_keywords": [],
                "special_features": []
            },
            "reasoning": "Fallback categories used due to LLM error"
        }


# Singleton instance
_llm_service_instance = None


def get_llm_service() -> LLMService:
    """Get or create the LLM service singleton"""
    global _llm_service_instance
    if _llm_service_instance is None:
        _llm_service_instance = LLMService()
    return _llm_service_instance
