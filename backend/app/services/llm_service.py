import os
import json
import logging
from typing import Dict, Any, Optional, List

# --- UPDATED IMPORTS ---
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage # Fixed import path

# Configure logging
logger = logging.getLogger("app.services.llm_service")

# ==========================================
# PART 1: Chatbot Logic (Added for Phase 3)
# ==========================================

async def generate_chat_response(
    message: str, 
    history: List[Dict[str, str]], 
    user_preferences: Dict[str, Any]
) -> str:
    """
    Generates a response from the LLM based on chat history and user preferences.
    Used by: backend/app/routes/chatbot.py
    """
    try:
        # 1. Construct the System Prompt
        system_prompt = _construct_system_prompt(user_preferences)
        
        # 2. Prepare the messages list for the LLM
        # Convert dict messages to LangChain message objects immediately
        lc_messages = [SystemMessage(content=system_prompt)]
        
        # Add recent history (limit to last 10 messages to save tokens)
        recent_history = history[-10:]
        for msg in recent_history:
            if msg["role"] == "user":
                lc_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                # LangChain uses AIMessage for assistant responses, 
                # but SystemMessage works for context injection if needed. 
                # strictly speaking, it should be AIMessage, but let's stick to base classes or Human/System for simplicity
                # unless you import AIMessage. Let's add AIMessage to imports if we want to be strict, 
                # or just represent history as Human/System pairs.
                # For simplicity here, we can just treat previous assistant answers as context.
                from langchain_core.messages import AIMessage
                lc_messages.append(AIMessage(content=msg["content"]))
        
        # Add the current message
        lc_messages.append(HumanMessage(content=message))
        
        # 3. Call the LLM via Cornell LiteLLM proxy
        chat = ChatOpenAI(
            openai_api_base=os.getenv("LITELLM_BASE_URL", "https://api.ai.it.cornell.edu"),
            model=os.getenv("LITELLM_MODEL", "openai.gpt-4o"),
            api_key=os.getenv("LITELLM_API_KEY", "missing-key"), # Ensure key is passed
            temperature=0.7,
            max_tokens=300,
        )

        # 4. Invoke the LLM (Updated from deprecated __call__ to invoke)
        response = chat.invoke(lc_messages)
        return response.content

    except Exception as e:
        logger.error(f"❌ LLM generation error: {str(e)}")
        return "I'm having a little trouble connecting to my creative brain right now. Could you ask that again?"

def _construct_system_prompt(prefs: Dict[str, Any]) -> str:
    """
    Helper function to turn the structured preference dictionary into 
    natural language for the System Prompt.
    """
    # Extract details with safe defaults
    cuisines = ", ".join(prefs.get("cuisines", [])) or "No specific preference"
    dietary = ", ".join(prefs.get("dietary_restrictions", [])) or "None"
    price = prefs.get("price_preference", "Any")
    
    # Format flavor profile (dictionary to string)
    flavors_dict = prefs.get("flavor_profile", {})
    if flavors_dict:
        flavors_str = ", ".join([f"{k}: {v}" for k, v in flavors_dict.items()])
    else:
        flavors_str = "Not specified"
        
    ambiance = ", ".join(prefs.get("ambiance_preference", [])) or "Not specified"
    notes = ", ".join(prefs.get("general_notes", [])) or "None"

    # Build the prompt
    prompt = f"""You are KindaLike, a friendly and knowledgeable restaurant recommendation AI.

Your goal is to help the user decide where to eat based on their unique taste profile.

=== USER TASTE PROFILE ===
- **Favorite Cuisines:** {cuisines}
- **Dietary Restrictions:** {dietary}
- **Price Preference:** {price}
- **Flavor Profile:** {flavors_str}
- **Ambiance/Vibe:** {ambiance}
- **General Notes:** {notes}

=== INSTRUCTIONS ===
1. **Be Personalized:** Use the profile above. If they love spicy food, mention spicy options. If they are vegan, strictly respect that.
2. **Be Conversational:** Talk like a helpful foodie friend, not a robot. Keep responses concise (2-3 sentences unless asked for more).
3. **Handle Missing Info:** If the profile is vague (e.g., "No specific preference"), ask clarifying questions to narrow down what they are in the mood for *right now*.
4. **Context Awareness:** You are chatting in real-time. Use the chat history to maintain context.

Answer the user's latest message now.
"""
    return prompt


# ==========================================
# PART 2: Existing Category Generation Logic
# ==========================================

class LLMService:
    """Service for generating restaurant categories using LLM"""

    def __init__(self):
        """Initialize the LLM service with LiteLLM configuration"""
        self.api_key = os.getenv("LITELLM_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.base_url = os.getenv("LITELLM_BASE_URL", "https://api.ai.it.cornell.edu")
        self.model = os.getenv("LITELLM_MODEL", "openai.gpt-4o")

        if not self.api_key:
            # Warn but don't crash immediately, allows app to start if key is missing
            logger.warning("LITELLM_API_KEY/OPENAI_API_KEY environment variable is not set")

        # Initialize ChatOpenAI with Cornell LiteLLM proxy
        # API key read automatically from OPENAI_API_KEY env var
        self.llm = ChatOpenAI(
            model=self.model,
            openai_api_base=self.base_url,
            api_key=self.api_key,
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
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                json_str = content[json_start:json_end].strip()
            elif "```" in content:
                json_start = content.find("```") + 3
                json_end = content.find("```", json_start)
                json_str = content[json_start:json_end].strip()
            else:
                json_str = content.strip()

            result = json.loads(json_str)

            # Validate the structure
            required_keys = ["hierarchical_categories", "primary_categories", "attributes"]
            if not all(key in result for key in required_keys):
                raise ValueError(f"LLM response missing required keys. Got: {result.keys()}")

            return result

        except Exception as e:
            print(f"Error generating categories: {e}")
            return self._get_fallback_categories(query, prefs)

    def _get_fallback_categories(
        self,
        query: str,
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fallback category generation if LLM fails"""
        cuisine = preferences.get("cuisine_type", "restaurants")
        price = preferences.get("price_range", "$$")
        
        price_map = {"$": 1, "$$": 2, "$$$": 3, "$$$$": 4}

        return {
            "hierarchical_categories": ["Food & Dining", "Restaurants", cuisine],
            "primary_categories": ["restaurants"],
            "attributes": {
                "cuisine_type": cuisine,
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