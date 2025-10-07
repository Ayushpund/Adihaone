# Personal Assistant

A Python-based personal assistant with Google search functionality and basic reminder system.

## Features

### 🔍 Google Search & News API
- Web search using web scraping (requests + BeautifulSoup)
- **News search using NewsAPI.org** - Reliable news from thousands of sources
- Returns search results with titles, snippets, and links
- Fallback to helpful suggestions when search fails
- Demo mode with sample data (no API key required for testing)

### 🔔 Basic Reminders
- Set reminders with natural language time parsing
- Support for various time formats:
  - "at 3 PM"
  - "in 2 hours" 
  - "tomorrow at 9 AM"
  - "in 30 minutes"
- SQLite database storage for persistence
- Check for due reminders

### 🤖 Basic Assistant Commands
- Time and date queries
- Mathematical calculations
- Weather information (requires API key)
- Greeting responses

## Installation

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables (optional):
```bash
# Create .env file with:
WOLFRAMALPHA_APP_ID=your_wolfram_app_id
OPENWEATHER_API_KEY=your_weather_api_key
NEWS_API_KEY=your_news_api_key
```

**Note**: For News API, get a free key from [NewsAPI.org](https://newsapi.org/) (1000 requests/day free)

3. Download spaCy language model:
```bash
python -m spacy download en_core_web_sm
```

## Usage

### Web Interface
```bash
python app.py
```
Then open http://localhost:5000 in your browser.

### Command Line Demo
```bash
python demo.py
```

### Example Commands

**Search Commands:**
- "Search for latest AI news"
- "Find python programming tutorials"
- "What is machine learning?"
- "Look up artificial intelligence"

**Reminder Commands:**
- "Remind me to call mom at 3 PM"
- "Set a reminder to buy groceries in 2 hours"
- "I need to take medicine in 30 minutes"
- "Remind me about the meeting tomorrow at 9 AM"

**Basic Commands:**
- "What time is it?"
- "What's today's date?"
- "Calculate 25 * 4"
- "Hello"

## File Structure

```
personal_assistant/
├── agent.py          # Main assistant logic
├── app.py           # Flask web application
├── demo.py          # Demo script
├── test_features.py # Test script
├── requirements.txt # Dependencies
├── templates/
│   └── index.html   # Web interface
├── static/
│   ├── css/         # Stylesheets
│   └── js/          # JavaScript
└── uploads/         # File uploads directory
```

## API Endpoints

- `GET /` - Main web interface
- `POST /ask` - Send text/voice commands
- `POST /speak` - Text-to-speech conversion

## Dependencies

- Flask - Web framework
- requests - HTTP requests
- BeautifulSoup4 - HTML parsing
- spaCy - Natural language processing
- pyttsx3 - Text-to-speech
- SpeechRecognition - Speech recognition
- python-dotenv - Environment variables
- sqlite3 - Database (built-in)

## Notes

- Search functionality uses web scraping and may be limited by anti-bot measures
- For production use, consider using official APIs (Google Custom Search API)
- Reminders are stored in SQLite database (`reminders.db`)
- Voice functionality requires microphone access
