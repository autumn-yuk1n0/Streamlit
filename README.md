# WeatherNow Chat — a conversational weather chatbot

A chat-style version of WeatherNow, built with Streamlit's native chat
components (`st.chat_message`, `st.chat_input`). Instead of a search box,
you talk to it: type a city name, or a question like *"will it rain in
Cebu today?"*, and it replies conversationally with current conditions,
today's range, and a plain-language umbrella recommendation.

Data comes from [Open-Meteo](https://open-meteo.com/) — free, no API key
needed.

## How it understands you

This is a lightweight rule-based chatbot (not an LLM) — it doesn't call any
external AI model. It:
1. Recognizes greetings ("hi", "hello") and a "help" request.
2. Otherwise extracts a likely city name from your message (handles phrasing
   like "weather in X", "will it rain in X today", or just a bare city name).
3. Looks up that city and fetches live weather, then writes a short
   conversational reply.

Try things like:
- `Manila`
- `weather in Cebu`
- `will it rain in Tandag today?`
- `help`

## Run locally (VS Code)

1. Open this folder in VS Code.
2. Open a terminal (`` Ctrl+` ``) and create/activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate      # Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run it:
   ```bash
   streamlit run app.py
   ```
5. It opens at `http://localhost:8501` with a chat window — type a city
   and hit Enter.

## Deploy it live (Streamlit Community Cloud — free)

1. Push this folder to a public GitHub repository.
2. Go to **https://share.streamlit.io**, sign in with GitHub.
3. Click **New app** → pick this repo/branch → set main file to `app.py`.
4. Click **Deploy**. You'll get a live link like
   `https://your-username-weathernow-chat.streamlit.app`.

## Verified before packaging

- `app.py` compiles with no syntax errors.
- The parsing/reply logic (`extract_city`, `umbrella_line`, `bot_reply`,
  `describe_weather`) was unit-tested directly — all checks passed.
- The Streamlit server was started and confirmed to respond `HTTP 200`
  with no tracebacks in the log.

## Files

- `app.py` — the chatbot application
- `requirements.txt` — Python dependencies
- `README.md` — this file
