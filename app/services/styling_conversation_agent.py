"""
Conversational Styling Agent for StylistAI
Handles multi-turn conversations to gather context before giving recommendations
"""

from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


class StylingConversationAgent:
    """Agent that asks questions to understand user's needs before recommending"""

    def __init__(self):
        self.questions = [
            {
                "id": "occasion",
                "question": "What's the occasion? Is it for work, casual outing, date night, or something else?",
                "field": "occasion",
                "type": "text"
            },
            {
                "id": "weather",
                "question": "What's the weather like today? Hot, cold, rainy, or mild?",
                "field": "weather",
                "type": "text"
            },
            {
                "id": "formality",
                "question": "How formal should it be? Very formal, business casual, smart casual, or completely casual?",
                "field": "formality",
                "type": "text"
            },
            {
                "id": "mood",
                "question": "What mood are you going for? Professional, relaxed, confident, creative, or something else?",
                "field": "mood",
                "type": "text"
            }
        ]

    async def start_conversation(self, user_id: str, initial_query: str) -> Dict:
        """
        Start a new styling conversation

        Args:
            user_id: User ID
            initial_query: User's initial request

        Returns:
            Initial response with first question
        """
        state = {
            "user_id": user_id,
            "initial_query": initial_query,
            "current_step": 0,
            "collected_context": {},
            "is_complete": False
        }

        # Return first question
        return {
            "next_question": self.questions[0]["question"],
            "current_step": self.questions[0]["id"],
            "is_complete": False,
            "state": state
        }

    async def process_response(
        self,
        user_id: str,
        user_message: str,
        current_state: Dict
    ) -> Dict:
        """
        Process user's response and ask next question or generate recommendations

        Args:
            user_id: User ID
            user_message: User's answer
            current_state: Current conversation state

        Returns:
            Next question or final recommendations
        """
        try:
            # Get current step
            current_step_idx = current_state.get("current_step", 0)

            # Save user's response
            if current_step_idx < len(self.questions):
                field = self.questions[current_step_idx]["field"]
                current_state["collected_context"][field] = user_message
                logger.info(f"Collected {field}: {user_message}")

            # Move to next step
            next_step = current_step_idx + 1

            # Check if we have all context
            if next_step >= len(self.questions):
                # All questions answered - generate recommendations
                current_state["is_complete"] = True
                current_state["current_step"] = "generating"

                return {
                    "next_question": "Perfect! Let me analyze your wardrobe and current trends to create the perfect outfit recommendations for you... 👔✨",
                    "current_step": "generating",
                    "is_complete": True,
                    "state": current_state
                }

            # Ask next question
            current_state["current_step"] = next_step
            next_question = self.questions[next_step]

            return {
                "next_question": next_question["question"],
                "current_step": next_question["id"],
                "is_complete": False,
                "state": current_state
            }

        except Exception as e:
            logger.error(f"Error processing response: {e}")
            return {
                "next_question": "Sorry, I encountered an error. Let's try again - what would you like styling advice for?",
                "current_step": "error",
                "is_complete": False,
                "state": current_state
            }

    async def generate_final_recommendations(
        self,
        user_id: str,
        context: Dict,
        user_preferences: Optional[Dict] = None
    ) -> Dict:
        """
        Generate final recommendations using collected context

        Args:
            user_id: User ID
            context: Collected context from conversation
            user_preferences: User's saved preferences

        Returns:
            Final recommendations
        """
        from app.services.langgraph_agent import run_styling_agent

        # Build enriched query from context
        initial_query = context.get("initial_query", "styling advice")
        occasion = context.get("occasion", "casual")
        weather = context.get("weather", "mild")
        formality = context.get("formality", "smart casual")
        mood = context.get("mood", "confident")

        enriched_query = f"""
I need {initial_query}.

Context:
- Occasion: {occasion}
- Weather: {weather}
- Formality level: {formality}
- Mood/vibe: {mood}

Please recommend specific outfits from my wardrobe that match this context,
and suggest any additional pieces that would complete the look based on current trends.
"""

        # Run the styling agent with enriched context
        result = await run_styling_agent(
            user_id=user_id,
            query=enriched_query,
            user_preferences=user_preferences
        )

        return result


# Global agent instance
_styling_conversation_agent = None


def get_styling_conversation_agent() -> StylingConversationAgent:
    """Get or create the styling conversation agent"""
    global _styling_conversation_agent
    if _styling_conversation_agent is None:
        _styling_conversation_agent = StylingConversationAgent()
    return _styling_conversation_agent
