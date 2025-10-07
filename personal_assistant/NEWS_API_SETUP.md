# News API Setup Guide

## Getting Started with News API

The personal assistant now uses NewsAPI.org for reliable news search functionality. Here's how to set it up:

### 1. Get a Free API Key

1. Visit [NewsAPI.org](https://newsapi.org/)
2. Click "Get API Key" 
3. Sign up for a free account
4. You'll get 1000 requests per day for free

### 2. Configure Your Environment

Create a `.env` file in the `personal_assistant` directory:

```bash
# Add this line to your .env file
NEWS_API_KEY=your_actual_api_key_here
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Test the Setup

```bash
python -c "import agent; print(agent.search_web('latest ai news'))"
```

## Current Demo Mode

Right now, the assistant is running in **demo mode** with sample news data. To get real-time news:

1. Get your API key from NewsAPI.org
2. Add it to your `.env` file
3. Restart the application

## Features

- **Real-time News**: Get the latest news from thousands of sources
- **Search by Topic**: Search for specific topics like "AI", "technology", "politics"
- **Multiple Sources**: News from various reputable sources
- **Published Dates**: See when articles were published
- **Direct Links**: Access full articles via provided links

## Example Commands

- "latest ai news"
- "search for technology news" 
- "what's the latest in machine learning"
- "find news about climate change"

## API Limits

- **Free Tier**: 1000 requests per day
- **Rate Limit**: 100 requests per hour
- **Sources**: 80,000+ articles from 80,000+ sources

## Troubleshooting

If you're getting sample data instead of real news:
1. Check your `.env` file has the correct API key
2. Verify the API key is valid at NewsAPI.org
3. Make sure you haven't exceeded your daily limit
4. Restart the application after adding the API key
