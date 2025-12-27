"""
Onboarding Agent for StylistAI
Collects user preferences and photos through conversational flow
"""

from typing import TypedDict, List, Optional, Annotated
from operator import add
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from app.config import settings
import json
import logging

logger = logging.getLogger(__name__)


# Define the onboarding state
class OnboardingState(TypedDict):
    """State for the onboarding conversation"""
    messages: Annotated[List[BaseMessage], add]
    user_id: str
    current_step: str
    collected_data: dict
    is_complete: bool


# Onboarding questions
ONBOARDING_STEPS = {
    "greeting": {
        "question": "👋 Welcome to StylistAI! I'm your personal AI stylist. To give you the best fashion advice, I'd like to learn about your style preferences. Shall we get started?",
        "next": "style_aesthetics"
    },
    "style_aesthetics": {
        "question": "What style aesthetics do you prefer? (e.g., minimalist, modern, classic, streetwear, bohemian, etc.)",
        "field": "style_aesthetics",
        "next": "colors"
    },
    "colors": {
        "question": "What are your favorite colors to wear? Please list 3-5 colors.",
        "field": "colors",
        "next": "occasions"
    },
    "occasions": {
        "question": "What occasions do you usually dress for? (e.g., work, casual outings, formal events, gym, dates)",
        "field": "occasions",
        "next": "fit_preferences"
    },
    "fit_preferences": {
        "question": "What fit do you prefer? (e.g., fitted, relaxed, oversized, slim)",
        "field": "fit_preferences",
        "next": "budget"
    },
    "budget": {
        "question": "What's your budget range? (e.g., budget-friendly, mid-range, premium, luxury)",
        "field": "budget",
        "next": "body_type"
    },
    "body_type": {
        "question": "What's your body type? (e.g., athletic, slim, curvy, tall, petite) - This helps me suggest better fits!",
        "field": "body_type",
        "next": "style_goals"
    },
    "style_goals": {
        "question": "What are your style goals? (e.g., look more professional, express creativity, stay comfortable, follow trends)",
        "field": "style_goals",
        "next": "photos"
    },
    "photos": {
        "question": "Great! Now, I'd love to see some photos of your current wardrobe or favorite outfits. This will help me understand your existing style and make better recommendations. You can upload 3-5 photos. Click the 'Upload Photos' button when ready!",
        "field": "photo_upload_requested",
        "next": "complete"
    },
    "complete": {
        "question": "Perfect! I've learned a lot about your style. Let's start creating amazing outfits together! 🎉",
        "next": None
    }
}


def start_onboarding(state: OnboardingState) -> OnboardingState:
    """Start the onboarding process"""
    logger.info(f"[Onboarding] Starting for user: {state['user_id']}")

    state['current_step'] = 'greeting'
    state['collected_data'] = {}
    state['is_complete'] = False

    greeting = ONBOARDING_STEPS['greeting']['question']
    state['messages'].append(AIMessage(content=greeting))

    return state


def process_user_response(state: OnboardingState) -> OnboardingState:
    """Process user's response and extract information"""
    logger.info(f"[Onboarding] Processing response for step: {state['current_step']}")

    # Get the last user message
    user_messages = [msg for msg in state['messages'] if isinstance(msg, HumanMessage)]
    if not user_messages:
        return state

    last_user_message = user_messages[-1].content

    # Get current step info
    step_info = ONBOARDING_STEPS.get(state['current_step'])
    if not step_info:
        return state

    # Extract and store the information using LLM
    if 'field' in step_info and step_info['field'] != 'photo_upload_requested':
        extracted_data = extract_preference_with_llm(
            user_response=last_user_message,
            field_name=step_info['field']
        )

        state['collected_data'][step_info['field']] = extracted_data
        logger.info(f"[Onboarding] Collected {step_info['field']}: {extracted_data}")

    return state


def extract_preference_with_llm(user_response: str, field_name: str) -> any:
    """Use LLM to extract structured data from user's natural language response"""

    llm = ChatOpenAI(
        model=settings.OPENAI_LLM_MODEL,
        api_key=settings.OPENAI_API_KEY,
        temperature=0.3
    )

    extraction_prompts = {
        "style_aesthetics": "Extract style aesthetics as a list. Examples: minimalist, modern, classic, streetwear, bohemian, vintage.",
        "colors": "Extract color names as a list. Examples: navy, black, white, grey, beige, olive.",
        "occasions": "Extract occasions as a list. Examples: work, casual, formal, gym, dates, business-casual.",
        "fit_preferences": "Extract fit preference. Examples: fitted, relaxed, oversized, slim, tailored.",
        "budget": "Extract budget range. Examples: budget-friendly, mid-range, premium, luxury.",
        "body_type": "Extract body type. Examples: athletic, slim, curvy, tall, petite, average.",
        "style_goals": "Extract style goals as a list. Examples: look professional, express creativity, stay comfortable, follow trends."
    }

    prompt = f"""
Extract {field_name} from this user response: "{user_response}"

Instruction: {extraction_prompts.get(field_name, 'Extract the information')}

Return ONLY a JSON object with a single key "{field_name}" containing the extracted value.
For lists, return an array. For single values, return a string.

Example formats:
- List: {{"{field_name}": ["value1", "value2"]}}
- Single: {{"{field_name}": "value"}}
"""

    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        # Parse JSON from response
        import re
        json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            return data.get(field_name, user_response)
    except Exception as e:
        logger.error(f"[Onboarding] Error extracting data: {e}")

    # Fallback: return raw response
    return user_response


def ask_next_question(state: OnboardingState) -> OnboardingState:
    """Ask the next question in the onboarding flow"""

    current_step_info = ONBOARDING_STEPS.get(state['current_step'])
    if not current_step_info:
        state['is_complete'] = True
        return state

    next_step = current_step_info['next']

    if next_step is None or next_step == 'complete':
        # Onboarding complete
        state['current_step'] = 'complete'
        state['is_complete'] = True

        completion_message = ONBOARDING_STEPS['complete']['question']
        state['messages'].append(AIMessage(content=completion_message))

        logger.info(f"[Onboarding] Completed for user: {state['user_id']}")
        logger.info(f"[Onboarding] Collected data: {state['collected_data']}")

        return state

    # Move to next step
    state['current_step'] = next_step
    next_question = ONBOARDING_STEPS[next_step]['question']
    state['messages'].append(AIMessage(content=next_question))

    return state


def route_onboarding(state: OnboardingState) -> str:
    """Route to next node or end"""
    if state['is_complete']:
        return "end"
    return "continue"


# Build the onboarding graph
def create_onboarding_agent() -> StateGraph:
    """Create the onboarding agent workflow"""

    workflow = StateGraph(OnboardingState)

    # Add nodes
    workflow.add_node("start", start_onboarding)
    workflow.add_node("process_response", process_user_response)
    workflow.add_node("ask_question", ask_next_question)

    # Set entry point
    workflow.set_entry_point("start")

    # Add edges
    workflow.add_edge("start", "ask_question")
    workflow.add_edge("process_response", "ask_question")

    # Conditional edge from ask_question
    workflow.add_conditional_edges(
        "ask_question",
        route_onboarding,
        {
            "continue": END,  # Wait for user response
            "end": END
        }
    )

    return workflow.compile()


# Main function to run onboarding
async def run_onboarding_agent(
    user_id: str,
    user_message: Optional[str] = None,
    current_state: Optional[dict] = None
) -> dict:
    """
    Run the onboarding agent

    Args:
        user_id: User's ID
        user_message: User's response (None for first interaction)
        current_state: Previous state (None for first interaction)

    Returns:
        Updated state with next question
    """

    agent = create_onboarding_agent()

    if current_state is None:
        # First interaction - start onboarding
        initial_state: OnboardingState = {
            "messages": [],
            "user_id": user_id,
            "current_step": "greeting",
            "collected_data": {},
            "is_complete": False
        }

        result = agent.invoke(initial_state)

    else:
        # Continue onboarding with user's response
        # Reconstruct BaseMessage objects from serialized messages
        messages = []
        for msg in current_state.get("messages", []):
            if isinstance(msg, dict):
                # Convert dict back to BaseMessage
                if msg.get("role") == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                else:
                    messages.append(AIMessage(content=msg["content"]))
            else:
                # Already a BaseMessage object
                messages.append(msg)

        state: OnboardingState = {
            "messages": messages,
            "user_id": user_id,
            "current_step": current_state.get("current_step", "greeting"),
            "collected_data": current_state.get("collected_data", {}),
            "is_complete": current_state.get("is_complete", False)
        }

        # Add user's message
        if user_message:
            state["messages"].append(HumanMessage(content=user_message))

        # Process response and ask next question
        state = process_user_response(state)
        state = ask_next_question(state)

        result = state

    # Convert to serializable format
    return {
        "user_id": result["user_id"],
        "current_step": result["current_step"],
        "is_complete": result["is_complete"],
        "collected_data": result["collected_data"],
        "messages": [
            {
                "role": "user" if isinstance(msg, HumanMessage) else "assistant",
                "content": msg.content
            }
            for msg in result["messages"]
        ],
        "next_question": result["messages"][-1].content if result["messages"] else None
    }


# Helper function to save onboarding data
def save_onboarding_data(user_id: str, data: dict):
    """Save collected onboarding data to user preferences"""
    from app.services.user_service import UserService

    preferences = {
        "style_aesthetics": data.get("style_aesthetics", []),
        "colors": data.get("colors", []),
        "occasions": data.get("occasions", []),
        "fit_preferences": data.get("fit_preferences", ""),
        "budget": data.get("budget", ""),
        "body_type": data.get("body_type", ""),
        "style_goals": data.get("style_goals", []),
        "onboarding_completed": True
    }

    UserService.save_user_preferences(user_id, preferences)
    logger.info(f"[Onboarding] Saved preferences for user: {user_id}")

    return preferences
