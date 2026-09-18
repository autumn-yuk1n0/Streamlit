"""
WeatherNow Chat — a conversational weather chatbot built with Streamlit.

Type a city name, or a question like "will it rain in Manila today?", and the
bot replies with current conditions, a plain-language umbrella call, and the
next few hours.

Data source: Open-Meteo (https://open-meteo.com/) — free, no API key required.
"""

import re
import streamlit as st
import requests
from datetime import datetime

st.set_page_config(page_title="WeatherNow Chat", page_icon="⛅", layout="centered")

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

WEATHER_CODES = {
    0: ("clear sky", "☀️"),
    1: ("mainly clear", "🌤️"),
    2: ("partly cloudy", "⛅"),
    3: ("overcast", "☁️"),
    45: ("foggy", "🌫️"),
    48: ("foggy with rime", "🌫️"),
    51: ("light drizzle", "🌦️"),
    53: ("moderate drizzle", "🌦️"),
    55: ("dense drizzle", "🌧️"),
    56: ("light freezing drizzle", "🌧️"),
    57: ("dense freezing drizzle", "🌧️"),
    61: ("slight rain", "🌦️"),
    63: ("moderate rain", "🌧️"),
    65: ("heavy rain", "🌧️"),
    66: ("light freezing rain", "🌧️"),
    67: ("heavy freezing rain", "🌧️"),
    71: ("slight snow", "🌨️"),
    73: ("moderate snow", "🌨️"),
    75: ("heavy snow", "❄️"),
    77: ("snow grains", "❄️"),
    80: ("slight rain showers", "🌦️"),
    81: ("moderate rain showers", "🌧️"),
    82: ("violent rain showers", "⛈️"),
    85: ("slight snow showers", "🌨️"),
    86: ("heavy snow showers", "❄️"),
    95: ("thunderstorms", "⛈️"),
    96: ("thunderstorms with slight hail", "⛈️"),
    99: ("thunderstorms with heavy hail", "⛈️"),
}

GREETINGS = {"hi", "hello", "hey", "yo", "sup", "hiya"}
HELP_WORDS = {"help", "what can you do", "how does this work", "commands"}

WELCOME_MESSAGE = (
    "Hi! I'm WeatherNow. Tell me a city name — like **Manila** or "
    "**\"will it rain in Cebu today?\"** — and I'll give you the current "
    "conditions and an umbrella call."
)


def describe_weather(code: int):
    return WEATHER_CODES.get(int(code), ("unknown conditions", "❔"))


@st.cache_data(ttl=600, show_spinner=False)
def geocode_city(city_name: str):
    resp = requests.get(
        GEOCODE_URL,
        params={"name": city_name, "count": 1, "language": "en", "format": "json"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json().get("results", [])


@st.cache_data(ttl=600, show_spinner=False)
def fetch_weather(lat: float, lon: float):
    resp = requests.get(
        FORECAST_URL,
        params={
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,apparent_temperature,precipitation,weathercode,is_day",
            "hourly": "temperature_2m,precipitation_probability,weathercode",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max",
            "timezone": "auto",
            "forecast_days": 2,
        },
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def extract_city(text: str) -> str:
    """Pull a likely city name out of a free-form chat message."""
    t = text.strip()
    # "weather in <city>", "weather for <city>", "in <city>"
    match = re.search(r"\bin\s+([A-Za-z\s,]+?)(?:\?|$|today|tomorrow|now)", t, re.IGNORECASE)
    if match:
        candidate = match.group(1).strip(" ,")
        if candidate:
            return candidate
    # Strip common question phrasing, fall back to the raw text as a city name.
    cleaned = re.sub(
        r"(what'?s|whats|how'?s|hows|is it going to rain|will it rain|"
        r"the weather|weather|today|tomorrow|now|please|\?)",
        "",
        t,
        flags=re.IGNORECASE,
    ).strip(" ,.!")
    return cleaned if cleaned else t


def umbrella_line(precip_chance, precip_now) -> str:
    if precip_now and precip_now > 0:
        return "It's raining there right now, so grab an umbrella. ☔"
    if precip_chance is not None and precip_chance >= 50:
        return f"There's a {precip_chance:.0f}% chance of rain today — I'd bring an umbrella. ☂️"
    if precip_chance is not None and precip_chance >= 20:
        return f"Only a {precip_chance:.0f}% chance of rain — a light umbrella wouldn't hurt, but it's optional."
    return "Rain looks unlikely today — no umbrella needed. 🕶️"


def build_weather_reply(city_query: str) -> str:
    try:
        matches = geocode_city(city_query)
    except requests.RequestException:
        return "I couldn't reach the weather service just now — please try again in a moment."

    if not matches:
        return f"I couldn't find a place called **{city_query}**. Could you check the spelling, or add a country?"

    place = matches[0]
    try:
        data = fetch_weather(place["latitude"], place["longitude"])
    except requests.RequestException:
        return "I found the location, but couldn't fetch the forecast just now — please try again."

    current = data.get("current", {})
    daily = data.get("daily", {})
    if not current:
        return "I found the location, but weather data wasn't available for it — please try again."

    temp = current.get("temperature_2m")
    feels_like = current.get("apparent_temperature")
    desc, emoji = describe_weather(current.get("weathercode", 0))
    precip_now = current.get("precipitation", 0)
    today_high = daily.get("temperature_2m_max", [None])[0]
    today_low = daily.get("temperature_2m_min", [None])[0]
    precip_chance = daily.get("precipitation_probability_max", [None])[0]

    place_label = ", ".join(
        p for p in [place.get("name"), place.get("admin1"), place.get("country")] if p
    )

    lines = [
        f"**{place_label}** {emoji}",
        f"It's currently **{temp:.0f}°C** with {desc}"
        + (f" (feels like {feels_like:.0f}°C)." if feels_like is not None else "."),
    ]
    if today_high is not None and today_low is not None:
        lines.append(f"Today's range: {today_low:.0f}°C to {today_high:.0f}°C.")
    lines.append(umbrella_line(precip_chance, precip_now))

    return "\n\n".join(lines)


def bot_reply(user_text: str) -> str:
    text_lower = user_text.strip().lower()
    if text_lower in GREETINGS:
        return "Hey there! Which city's weather would you like to know?"
    if any(h in text_lower for h in HELP_WORDS):
        return WELCOME_MESSAGE
    city_query = extract_city(user_text)
    if not city_query:
        return "I didn't catch a city name — could you tell me which city you mean?"
    return build_weather_reply(city_query)


def main():
    st.title("⛅ WeatherNow Chat")
    st.caption("Ask about the weather anywhere, conversationally.")

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": WELCOME_MESSAGE}]

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("Ask about the weather, e.g. \"will it rain in Cebu today?\"")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Checking the sky..."):
                reply = bot_reply(user_input)
            st.markdown(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})

    if st.session_state.messages and len(st.session_state.messages) > 1:
        if st.button("Clear conversation"):
            st.session_state.messages = [{"role": "assistant", "content": WELCOME_MESSAGE}]
            st.rerun()

    st.caption(f"Weather data by Open-Meteo.com · {datetime.now().strftime('%I:%M %p')}")


if __name__ == "__main__":
    main()
