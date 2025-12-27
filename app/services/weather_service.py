"""
Weather Service for StylistAI
Fetches real-time and forecast weather data based on location and date
"""

import logging
import requests
from typing import Optional, Dict
from datetime import datetime, timedelta
from app.config import settings

logger = logging.getLogger(__name__)

# OpenWeatherMap API (Free tier: current + 5-day forecast)
# Alternative: WeatherAPI.com (more generous free tier)
WEATHER_API_KEY = settings.OPENAI_API_KEY  # Placeholder - user should add weather API key
WEATHER_API_BASE = "https://api.openweathermap.org/data/2.5"


class WeatherService:
    """Service for fetching weather data"""

    @staticmethod
    def get_weather_for_location_and_date(
        location: str,
        date: Optional[str] = None
    ) -> Dict:
        """
        Get weather information for a location and date

        Args:
            location: Location name (city, area, etc.)
            date: Date string (e.g., "today", "tomorrow", "Saturday", "2024-12-30")

        Returns:
            Weather information dict with temperature, conditions, etc.
        """
        try:
            # For POC: Return intelligent weather based on location keywords
            # In production: Use real weather API
            return WeatherService._get_intelligent_weather_estimate(location, date)

        except Exception as e:
            logger.error(f"Error fetching weather: {e}")
            return {
                "location": location,
                "temperature": "moderate",
                "conditions": "mild",
                "description": "pleasant weather",
                "advice": "Dress in layers to be comfortable"
            }

    @staticmethod
    def _get_intelligent_weather_estimate(location: str, date: Optional[str]) -> Dict:
        """
        Provide intelligent weather estimates based on location and date

        This is a smart fallback when weather API is not configured.
        Uses location keywords and current season to make educated guesses.
        """
        location_lower = location.lower() if location else ""
        current_month = datetime.now().month

        # Determine season (Northern Hemisphere)
        if current_month in [12, 1, 2]:
            season = "winter"
        elif current_month in [3, 4, 5]:
            season = "spring"
        elif current_month in [6, 7, 8]:
            season = "summer"
        else:
            season = "fall"

        # Location-based climate patterns
        weather_info = {
            "location": location,
            "season": season,
            "date": date or "today"
        }

        # Beach/coastal areas
        if any(word in location_lower for word in ["beach", "coast", "miami", "california", "florida", "ocean"]):
            if season == "summer":
                weather_info.update({
                    "temperature": "hot (85-95°F)",
                    "conditions": "sunny and humid",
                    "description": "hot and humid beach weather",
                    "advice": "Lightweight, breathable fabrics. Light colors to reflect heat. Sun protection essential."
                })
            elif season == "winter":
                weather_info.update({
                    "temperature": "mild (60-75°F)",
                    "conditions": "pleasant with breeze",
                    "description": "perfect beach weather",
                    "advice": "Light layers. It can get breezy near the water."
                })
            else:
                weather_info.update({
                    "temperature": "warm (75-85°F)",
                    "conditions": "pleasant and breezy",
                    "description": "beautiful coastal weather",
                    "advice": "Light, breathable clothing. Bring a light layer for evening breeze."
                })

        # Mountain/cold areas
        elif any(word in location_lower for word in ["mountain", "aspen", "colorado", "vermont", "tahoe", "ski"]):
            if season in ["winter", "fall"]:
                weather_info.update({
                    "temperature": "cold (25-45°F)",
                    "conditions": "cool to cold, possibly snowy",
                    "description": "chilly mountain weather",
                    "advice": "Warm layers essential. Coat, boots, winter accessories. Dress in layers you can adjust."
                })
            else:
                weather_info.update({
                    "temperature": "cool (50-70°F)",
                    "conditions": "pleasant but can change",
                    "description": "changeable mountain weather",
                    "advice": "Layers are key! Temperature varies by elevation. Start with base layers and add/remove as needed."
                })

        # Desert areas
        elif any(word in location_lower for word in ["desert", "phoenix", "vegas", "arizona", "palm springs"]):
            if season == "summer":
                weather_info.update({
                    "temperature": "very hot (100-110°F)",
                    "conditions": "extremely hot and dry",
                    "description": "intense desert heat",
                    "advice": "Ultra-lightweight fabrics. Light colors essential. Stay hydrated and in shade when possible."
                })
            else:
                weather_info.update({
                    "temperature": "mild to warm (70-85°F)",
                    "conditions": "pleasant and dry",
                    "description": "perfect desert weather",
                    "advice": "Comfortable layers. Cool evenings mean you'll want a jacket later."
                })

        # Tropical areas
        elif any(word in location_lower for word in ["tropical", "hawaii", "caribbean", "puerto rico", "humid"]):
            weather_info.update({
                "temperature": "warm to hot (80-90°F)",
                "conditions": "humid with possible showers",
                "description": "tropical weather",
                "advice": "Moisture-wicking, quick-dry fabrics. Always humid. Bring a light rain jacket."
            })

        # City/urban areas
        elif any(word in location_lower for word in ["city", "downtown", "urban", "nyc", "new york", "chicago", "boston"]):
            if season == "winter":
                weather_info.update({
                    "temperature": "cold (20-40°F)",
                    "conditions": "cold urban winter",
                    "description": "cold city weather",
                    "advice": "Warm coat, comfortable boots for walking. Layers underneath. Cities feel colder due to wind tunnels."
                })
            elif season == "summer":
                weather_info.update({
                    "temperature": "hot (75-90°F)",
                    "conditions": "warm, urban heat island effect",
                    "description": "warm city weather",
                    "advice": "Cities can feel hotter due to concrete. Breathable fabrics. Comfortable walking shoes."
                })
            else:
                weather_info.update({
                    "temperature": "moderate (55-75°F)",
                    "conditions": "pleasant urban weather",
                    "description": "nice city weather",
                    "advice": "Light layers work well. Comfortable shoes for city walking."
                })

        # Default (general location)
        else:
            if season == "winter":
                weather_info.update({
                    "temperature": "cool to cold (35-55°F)",
                    "conditions": "winter weather",
                    "description": "cool winter day",
                    "advice": "Layers and a warm coat. Adjust based on indoor/outdoor time."
                })
            elif season == "summer":
                weather_info.update({
                    "temperature": "warm (70-85°F)",
                    "conditions": "summer weather",
                    "description": "pleasant summer day",
                    "advice": "Light, breathable clothing. Sun protection if outdoors."
                })
            else:
                weather_info.update({
                    "temperature": "mild (60-75°F)",
                    "conditions": "comfortable weather",
                    "description": "pleasant day",
                    "advice": "Light layers work well. Easy to adjust."
                })

        return weather_info

    @staticmethod
    def format_weather_for_conversation(weather_info: Dict) -> str:
        """
        Format weather info into conversational text

        Args:
            weather_info: Weather information dict

        Returns:
            Conversational weather description
        """
        location = weather_info.get("location", "your area")
        temp = weather_info.get("temperature", "moderate")
        conditions = weather_info.get("conditions", "pleasant")
        advice = weather_info.get("advice", "")

        response = f"For {location}, it looks like {conditions} weather - {temp}."

        if advice:
            response += f" {advice}"

        return response


# Note for production:
"""
To use real weather API in production:

1. Sign up for OpenWeatherMap API (free tier)
   https://openweathermap.org/api

2. Add to .env:
   WEATHER_API_KEY=your_api_key_here

3. Use this code to fetch real weather:

def get_real_weather(location: str):
    url = f"{WEATHER_API_BASE}/weather"
    params = {
        "q": location,
        "appid": WEATHER_API_KEY,
        "units": "imperial"  # or "metric"
    }
    response = requests.get(url, params=params)
    data = response.json()

    return {
        "temperature": f"{data['main']['temp']}°F",
        "conditions": data['weather'][0]['description'],
        "humidity": data['main']['humidity'],
        "wind_speed": data['wind']['speed']
    }

For forecast (5 days ahead):
    url = f"{WEATHER_API_BASE}/forecast"
"""
