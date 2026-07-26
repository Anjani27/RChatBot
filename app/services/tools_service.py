"""Tools service — weather and web search implementations."""
import os
import requests
from tavily import TavilyClient
from app.core.config import TAVILY_API_KEY, OPENWEATHER_API_KEY


def get_weather(location: str) -> str:
    """Fetch current weather from OpenWeatherMap."""
    if not OPENWEATHER_API_KEY:
        return "Weather tool unavailable: OPENWEATHER_API_KEY is missing."
    try:
        response = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"q": location, "appid": OPENWEATHER_API_KEY, "units": "metric"},
            timeout=8,
        )
        data = response.json()
        if response.status_code != 200:
            return f"Weather data unavailable for {location}: {data.get('message', 'unknown error')}"

        temp = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]
        humidity = data["main"]["humidity"]
        condition = data["weather"][0]["description"]
        return (
            f"Current weather in {location}: {temp}°C, "
            f"feels like {feels_like}°C, humidity {humidity}%, "
            f"condition: {condition}."
        )
    except requests.Timeout:
        return "Weather tool timed out. Please try again."
    except Exception as e:
        return f"Weather tool failed: {e}"


def web_search(query: str, max_results: int = 5) -> str:
    """Search the web using Tavily."""
    if not TAVILY_API_KEY:
        return "Web search unavailable: TAVILY_API_KEY is missing."
    try:
        client = TavilyClient(api_key=TAVILY_API_KEY)
        results = client.search(
            query=query,
            search_depth="basic",
            max_results=max_results,
            include_answer=True,
        )
        answer = results.get("answer", "")
        items = results.get("results", [])
        context = f"Search Summary:\n{answer}\n\n" if answer else ""
        for item in items:
            context += f"Title: {item.get('title', '')}\nURL: {item.get('url', '')}\nContent: {item.get('content', '')}\n\n"
        return context.strip() or "No useful web search results found."
    except Exception as e:
        return f"Web search failed: {e}"
