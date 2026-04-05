import os
import requests
import asyncio
import logging
from dotenv import load_dotenv
from livekit.agents import function_tool

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def get_current_city() -> str:
    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, lambda: requests.get("https://ipinfo.io", timeout=5))
        data = response.json()
        return data.get("city", "Unknown")
    except Exception:
        return "Unknown"


@function_tool
async def get_weather(city: str = "") -> str:
    """
    Gives current weather information for a given city.

    Use this tool when the user asks about weather, rain, temperature, humidity, or wind.
    If no city is given, detect city automatically.

    Example prompts:
    - "weather enna irukku?"
    - "What is the weather in Chennai?"
    - "Bangalore weather sollu"
    """
    api_key = os.getenv("OPENWEATHER_API_KEY")

    if not api_key:
        logger.error("OpenWeather API key missing.")
        return "OpenWeather API key not found in environment variables."

    if not city:
        city = await get_current_city()

    logger.info(f"Fetching weather for city: {city}")

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": api_key,
        "units": "metric"
    }

    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, lambda: requests.get(url, params=params, timeout=10))

        if response.status_code != 200:
            logger.error(f"OpenWeather API error: {response.status_code} - {response.text}")
            return f"Could not fetch weather for {city}. Please check the city name."

        data = response.json()
        weather = data["weather"][0]["description"].title()
        temperature = data["main"]["temp"]
        humidity = data["main"]["humidity"]
        wind_speed = data["wind"]["speed"]

        result = (
            f"Weather in {city}:\n"
            f"- Condition: {weather}\n"
            f"- Temperature: {temperature}°C\n"
            f"- Humidity: {humidity}%\n"
            f"- Wind Speed: {wind_speed} m/s"
        )

        logger.info(f"Weather result:\n{result}")
        return result

    except Exception as e:
        logger.exception(f"Exception while fetching weather: {e}")
        return "An error occurred while fetching the weather."