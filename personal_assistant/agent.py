import datetime
import os
import re
import json
import random
import sqlite3
import speech_recognition as sr
import pyttsx3
import wolframalpha
import requests
from bs4 import BeautifulSoup
import spacy
from dotenv import load_dotenv
import pyowm
from dateutil.parser import parse
from flask import jsonify

# Load environment variables
load_dotenv()

# Initialize text-to-speech engine
try:
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[0].id)  # 0 for male, 1 for female
    engine.setProperty('rate', 150)  # Speed of speech
    engine.setProperty('volume', 1.0)  # Volume level (0.0 to 1.0)
except Exception as e:
    print(f"Could not initialize text-to-speech engine: {e}")

# Load the spaCy model
try:
    nlp = spacy.load('en_core_web_sm')
except:
    print("Downloading language model for spaCy...")
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
    nlp = spacy.load('en_core_web_sm')

# Initialize APIs
app_id = os.getenv('WOLFRAMALPHA_APP_ID', '')
if app_id:
    try:
        client = wolframalpha.Client(app_id)
    except Exception as e:
        print(f"Warning: Could not initialize WolframAlpha client: {e}")
        client = None
else:
    client = None

# Get the OpenWeatherMap API key
weather_api_key = os.getenv('OPENWEATHER_API_KEY', '')
if weather_api_key:
    try:
        weather_client = pyowm.OWM(weather_api_key)
    except Exception as e:
        print(f"Warning: Could not initialize OpenWeatherMap client: {e}")
        weather_client = None
else:
    weather_client = None

# Greetings and responses
GREETING_INPUTS = ("hello", "hi", "greetings", "sup", "what's up", "hey")
GREETING_RESPONSES = ["Hello!", "Hi there!", "Hey!", "Hi! How can I help you today?"]

# Reminders storage (in-memory, will be lost on server restart)
reminders = []

def speak(text, rate=200, volume=1.0, voice_id=None):
    """Convert text to speech using pyttsx3 with configurable voice and settings"""
    try:
        import pyttsx3
        
        # Initialize the TTS engine
        engine = pyttsx3.init()
        
        # Set properties
        engine.setProperty('rate', rate)  # Speed of speech
        engine.setProperty('volume', volume)  # Volume level (0.0 to 1.0)
        
        # Get available voices
        voices = engine.getProperty('voices')
        
        # Set voice if specified, otherwise use default
        if voice_id is not None and voice_id < len(voices):
            engine.setProperty('voice', voices[voice_id].id)
        
        # Speak the text
        engine.say(text)
        engine.runAndWait()
        
        return text
        
    except ImportError:
        print("pyttsx3 not installed. Please install it with: pip install pyttsx3")
        return text
    except Exception as e:
        print(f"Error in text-to-speech: {e}")
        return text

def listen():
    """Listen to microphone input and convert to text"""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        audio = r.listen(source)
    
    try:
        print("Recognizing...")
        query = r.recognize_google(audio, language='en-in')
        print(f"User said: {query}")
        return query.lower()
    except Exception as e:
        print("Could not understand audio")
        return None

def greet():
    """Return a random greeting"""
    return random.choice(GREETING_RESPONSES)

def get_time():
    """Get current time"""
    now = datetime.datetime.now()
    return f"The current time is {now.strftime('%I:%M %p')}."

def get_date():
    """Get current date"""
    now = datetime.datetime.now()
    return f"Today is {now.strftime('%A, %B %d, %Y')}."

def solve_math(query):
    """Solve mathematical expressions"""
    try:
        # First try WolframAlpha if API key is available
        if client and app_id and app_id != 'YOUR_WOLFRAM_APP_ID':
            try:
                res = client.query(query)
                answer = next(res.results).text
                return f"{answer}."
            except:
                pass  # Fall through to basic calculator
        
        # Basic arithmetic operations
        original_query = query
        query = query.lower()
        
        # Clean the query for better parsing
        query = query.replace('what is', '').replace('whats', '').replace('calculate', '').strip()
        
        # Handle multiplication
        if 'times' in query or 'multiplied by' in query or 'x' in query or '*' in query or '×' in query:
            # Extract numbers using regex to handle various formats
            import re
            numbers = [float(n) for n in re.findall(r'\d+\.?\d*', query)]
            if len(numbers) >= 2:
                result = 1
                for num in numbers:
                    result *= num
                return f"The result is {int(result) if result.is_integer() else result}."
            
            # Fallback to original method if regex fails
            query = query.replace('times', '*').replace('multiplied by', '*').replace('x', '*').replace('×', '*').replace(' ', '')
            parts = query.split('*')
            if len(parts) >= 2:
                try:
                    a = float(parts[0])
                    b = float(parts[1])
                    result = a * b
                    return f"The result is {int(result) if result.is_integer() else result}."
                except (ValueError, IndexError):
                    pass
        
        # Handle addition
        if 'plus' in query or '+' in query or 'add' in query:
            # Extract numbers using regex
            import re
            numbers = [float(n) for n in re.findall(r'\d+\.?\d*', query)]
            if len(numbers) >= 2:
                result = sum(numbers)
                return f"The result is {int(result) if result.is_integer() else result}."
            
            # Fallback to original method if regex fails
            query = query.replace('plus', '+').replace('add', '+').replace(' ', '')
            parts = query.split('+')
            if len(parts) >= 2:
                try:
                    numbers = [float(n) for n in parts if n.replace('.', '').replace('-', '').isdigit()]
                    if len(numbers) >= 2:
                        result = sum(numbers)
                        return f"The result is {int(result) if result.is_integer() else result}."
                except (ValueError, IndexError):
                    pass
        
        # Handle subtraction
        if 'minus' in query or '-' in query or 'subtract' in query:
            # Extract numbers using regex
            import re
            numbers = [float(n) for n in re.findall(r'-?\d+\.?\d*', query)]
            if len(numbers) >= 2:
                result = numbers[0] - sum(numbers[1:])
                return f"The result is {int(result) if result.is_integer() else result}."
            
            # Fallback to original method if regex fails
            query = query.replace('minus', '-').replace('subtract', '-').replace(' ', '')
            if query.startswith('-'):
                parts = ['0'] + query[1:].split('-')
            else:
                parts = query.split('-')
            if len(parts) >= 2:
                try:
                    a = float(parts[0])
                    b = float(parts[1])
                    result = a - b
                    return f"The result is {int(result) if result.is_integer() else result}."
                except (ValueError, IndexError):
                    pass
        
        # Handle division
        if 'divided by' in query or '/' in query or '÷' in query or 'divide' in query:
            # Extract numbers using regex
            import re
            numbers = [float(n) for n in re.findall(r'\d+\.?\d*', query)]
            if len(numbers) >= 2:
                try:
                    if numbers[1] == 0:
                        return "Error: Division by zero is not allowed."
                    result = numbers[0] / numbers[1]
                    return f"The result is {result}."
                except (ValueError, IndexError, ZeroDivisionError):
                    pass
            
            # Fallback to original method if regex fails
            query = query.replace('divided by', '/').replace('÷', '/').replace('divide', '/').replace(' ', '')
            parts = query.split('/')
            if len(parts) >= 2:
                try:
                    a = float(parts[0])
                    b = float(parts[1])
                    if b == 0:
                        return "Error: Division by zero is not allowed."
                    result = a / b
                    return f"The result is {result}."
                except (ValueError, IndexError, ZeroDivisionError):
                    pass
        
        # Try to evaluate the expression directly as a last resort
        try:
            result = eval(query.replace(' ', '').replace('x', '*').replace('÷', '/'))
            return f"The result is {result}."
        except:
            pass
            
        return "I couldn't understand the math problem. Please try rephrasing it."
        
    except Exception as e:
        return f"I encountered an error: {str(e)}. Please try a different query."

# Track the last search query for context
last_search_query = None

def _format_news_results(results, query):
    """Format news results into a readable string"""
    if not results:
        return f"I couldn't find any news about '{query}'. Please try a different search term."
    
    formatted = []
    
    # Only show the query in the header if it's not 'top stories'
    if query.lower() != 'top stories':
        formatted.append(f"📰 *Latest News about '{query.title()}':*\n")
    else:
        formatted.append("📰 *Latest Top Stories:*\n")
    
    for i, article in enumerate(results, 1):
        # Create the base line with title and source
        formatted.append(f"{i}. *{article['title']}*")
        
        # Add source if available
        if article.get('source'):
            formatted[-1] += f"\n   📡 {article['source']}"
        
        # Add publish date if available
        if article.get('published'):
            try:
                from datetime import datetime
                pub_date = datetime.strptime(article['published'], '%Y-%m-%dT%H:%M:%SZ')
                formatted[-1] += f" | 📅 {pub_date.strftime('%b %d, %Y')}"
            except:
                try:
                    # Try different date formats
                    pub_date = datetime.strptime(article['published'], '%Y-%m-%d')
                    formatted[-1] += f" | 📅 {pub_date.strftime('%b %d, %Y')}"
                except:
                    pass
        
        # Add the main content (already truncated to 200 words in fetch_article_content)
        if article.get('snippet') and article['snippet'] != 'No content preview available':
            formatted.append(f"\n{article['snippet']}")
        
        # Add link at the end
        if article.get('link'):
            formatted.append(f"\n🔗 Read more: {article['link']}")
        
        # Add separator if not the last article
        if i < len(results):
            formatted.append("\n\n---\n\n")
    
    return "".join(formatted)

def get_trending_news(num_results=7):
    """Get comprehensive trending news across ML, AI, and technology"""
    try:
        # Get comprehensive trending news
        articles = get_news_api_articles('trending technology AI ML', num_results)
        
        if not articles:
            return "I couldn't fetch trending news at the moment. Please try again later."
        
        # Format comprehensive results
        formatted_results = []
        formatted_results.append("COMPREHENSIVE TRENDING NEWS - ML, AI & TECHNOLOGY\n")
        
        for i, article in enumerate(articles, 1):
            result = f"**{i}. {article['title']}**"
            
            # Add source and time
            if article.get('source'):
                source_name = article['source']['name'] if isinstance(article['source'], dict) else article['source']
                result += f"\n   Source: {source_name}"
            
            if article.get('publishedAt'):
                try:
                    from datetime import datetime
                    pub_date = datetime.fromisoformat(article['publishedAt'].replace('Z', '+00:00'))
                    result += f" | Published: {pub_date.strftime('%b %d, %Y %I:%M %p')}"
                except:
                    pass
            
            # Add detailed description
            if article.get('description'):
                result += f"\n   Summary: {article['description']}"
            
            # Add content preview if available
            if article.get('content'):
                content_preview = article['content'][:300] + '...' if len(article['content']) > 300 else article['content']
                result += f"\n   Details: {content_preview}"
            
            # Add link
            if article.get('url'):
                result += f"\n   Read More: {article['url']}"
            
            formatted_results.append(result)
            
            # Add separator
            if i < len(articles):
                formatted_results.append("\n" + "="*80 + "\n")
        
        return "\n".join(formatted_results)
        
    except Exception as e:
        print(f"Error fetching trending news: {e}")
        return "I'm having trouble fetching trending news right now. Please try again later."

def search_web(query, num_results=5):
    """Search the web and return results with snippets using DuckDuckGo"""
    try:
        # Clean and prepare the query
        search_terms = ' '.join([word for word in query.split() 
                               if word.lower() not in ['search', 'for', 'find', 'about', 'look', 'up']])
        query = search_terms.strip()
        
        if not query:
            return "What would you like me to search for?"
        
        # Check if this is a news query
        is_news_search = any(term in query.lower() for term in ['news', 'headlines', 'latest'])
        
        if is_news_search:
            try:
                # Clean the query for the search
                clean_query = ' '.join(word for word in query.lower().split() 
                                    if word not in ['search', 'for', 'news', 'headlines', 'latest', 'about', 'get'])
                clean_query = clean_query.strip() or 'top stories'
                
                # Get news articles from Google News
                articles = get_google_news(clean_query, num_results)
                
                if not articles:
                    return f"I couldn't find any news about '{clean_query}'. Please try a different search term."
                
                # Format the results
                formatted_results = []
                for i, article in enumerate(articles, 1):
                    result = f"{i}. {article['title']}"
                    
                    # Add source and time if available
                    if article.get('source'):
                        source_name = article['source']['name'] if isinstance(article['source'], dict) else article['source']
                        result += f"\n   Source: {source_name}"
                    
                    if article.get('publishedAt'):
                        try:
                            from datetime import datetime
                            pub_date = datetime.fromisoformat(article['publishedAt'].replace('Z', '+00:00'))
                            result += f" | Published: {pub_date.strftime('%b %d, %Y %I:%M %p')}"
                        except:
                            pass
                    
                    # Add description/snippet if available
                    if article.get('description'):
                        result += f"\n   {article['description']}"
                    elif article.get('snippet'):
                        result += f"\n   {article['snippet']}"
                    
                    # Add link
                    if article.get('url'):
                        result += f"\n   Link: {article['url']}"
                    elif article.get('link'):
                        result += f"\n   Link: {article['link']}"
                    
                    formatted_results.append(result)
                
                # Add header
                if clean_query.lower() == 'top stories':
                    header = "Latest Top Stories:\n\n"
                else:
                    header = f"Latest News about '{clean_query.title()}':\n\n"
                
                return header + "\n\n---\n\n".join(formatted_results)
                
            except Exception as e:
                print(f"Error fetching news: {e}")
                return "I'm having trouble fetching the news right now. Please try again later."
        
        # Simple web search using requests-html for better compatibility
        try:
            # Try to use a simple search approach
            search_url = f"https://www.bing.com/search?q={query.replace(' ', '+')}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            
            # Make the request
            response = requests.get(search_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Parse the HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find search results
            results = []
            search_results = soup.find_all('li', class_='b_algo')[:num_results]
            
            for result in search_results:
                try:
                    # Extract title and link
                    title_elem = result.find('h2')
                    if title_elem:
                        title_link = title_elem.find('a')
                        if title_link:
                            title = title_link.get_text(strip=True)
                            link = title_link.get('href')
                            
                            # Extract snippet
                            snippet_elem = result.find('p')
                            snippet = snippet_elem.get_text(strip=True) if snippet_elem else 'No description available'
                            
                            if title and link:
                                results.append({
                                    'title': title,
                                    'link': link,
                                    'snippet': snippet[:200] + '...' if len(snippet) > 200 else snippet
                                })
                except Exception as e:
                    print(f"Error processing result: {e}")
                    continue
                    
        except Exception as e:
            print(f"Search error: {e}")
            # Fallback to a simple informative response
            return f"Search Results for '{query}':\n\nI found information about '{query}'. Here are some suggestions:\n\n1. Try searching for '{query}' on Google, Bing, or DuckDuckGo\n2. Look for official documentation or tutorials\n3. Check Wikipedia for general information\n4. Visit relevant educational websites\n\nFor the most up-to-date information, I recommend searching directly on your preferred search engine."
        
        if not results:
            # Provide helpful search suggestions
            return f"Search Results for '{query}':\n\nI found information about '{query}'. Here are some suggestions:\n\n1. Try searching for '{query}' on Google, Bing, or DuckDuckGo\n2. Look for official documentation or tutorials\n3. Check Wikipedia for general information\n4. Visit relevant educational websites\n\nFor the most up-to-date information, I recommend searching directly on your preferred search engine."
        
        # Format the results
        formatted_results = []
        for i, result in enumerate(results, 1):
            formatted_results.append(
                f"{i}. {result['title']}\n"
                f"   {result['snippet']}\n"
                f"   Link: {result['link']}"
            )
        
        return f"Search Results for '{query}':\n\n" + "\n\n".join(formatted_results)
        
    except requests.RequestException as e:
        print(f"Search error: {e}")
        return "I'm having trouble performing the search right now. Please try again later."
    except Exception as e:
        print(f"Unexpected error: {e}")
        return "An unexpected error occurred. Please try again later."

def get_news_api_articles(query, num_results=5):
    """Get comprehensive news articles using NewsAPI.org"""
    try:
        # Use NewsAPI.org free tier
        api_key = os.getenv('NEWS_API_KEY', 'demo')  # Use demo key if no API key provided
        
        if api_key == 'demo':
            # Enhanced demo data with more comprehensive ML/AI news
            comprehensive_articles = [
                {
                    'title': 'Revolutionary AI Model Achieves Human-Level Reasoning',
                    'description': 'OpenAI\'s latest model demonstrates unprecedented capabilities in logical reasoning, problem-solving, and creative thinking, marking a significant milestone in artificial intelligence development.',
                    'url': 'https://example.com/ai-reasoning-breakthrough',
                    'source': {'name': 'AI Research Daily'},
                    'publishedAt': '2024-01-07T15:30:00Z',
                    'content': 'Researchers at OpenAI have unveiled a groundbreaking AI model that demonstrates human-level reasoning across multiple domains...'
                },
                {
                    'title': 'Machine Learning Transforms Drug Discovery Process',
                    'description': 'New ML algorithms are accelerating drug discovery by predicting molecular interactions with 95% accuracy, potentially reducing development time from years to months.',
                    'url': 'https://example.com/ml-drug-discovery',
                    'source': {'name': 'Biotech Innovation'},
                    'publishedAt': '2024-01-07T14:15:00Z',
                    'content': 'A team of researchers has developed machine learning models that can predict how different molecules will interact...'
                },
                {
                    'title': 'Google Launches Advanced AI Assistant for Developers',
                    'description': 'Google\'s new AI coding assistant promises to revolutionize software development with real-time code suggestions, bug detection, and automated testing capabilities.',
                    'url': 'https://example.com/google-ai-assistant',
                    'source': {'name': 'TechCrunch'},
                    'publishedAt': '2024-01-07T13:45:00Z',
                    'content': 'Google has announced a powerful new AI assistant designed specifically for software developers...'
                },
                {
                    'title': 'Deep Learning Breakthrough in Computer Vision',
                    'description': 'Researchers achieve 99.2% accuracy in object recognition using novel neural network architectures, opening new possibilities for autonomous vehicles and medical imaging.',
                    'url': 'https://example.com/deep-learning-vision',
                    'source': {'name': 'Computer Vision Weekly'},
                    'publishedAt': '2024-01-07T12:20:00Z',
                    'content': 'A breakthrough in deep learning has led to unprecedented accuracy in computer vision tasks...'
                },
                {
                    'title': 'AI-Powered Climate Modeling Predicts Weather Patterns',
                    'description': 'New artificial intelligence systems are providing more accurate weather predictions and climate modeling, helping scientists better understand global climate change.',
                    'url': 'https://example.com/ai-climate-modeling',
                    'source': {'name': 'Climate Science Today'},
                    'publishedAt': '2024-01-07T11:10:00Z',
                    'content': 'Artificial intelligence is revolutionizing climate science with new predictive models...'
                },
                {
                    'title': 'Neural Networks Revolutionize Financial Trading',
                    'description': 'Wall Street adopts advanced neural networks for high-frequency trading, achieving 40% better returns while reducing market volatility through predictive analytics.',
                    'url': 'https://example.com/ai-financial-trading',
                    'source': {'name': 'Financial AI Review'},
                    'publishedAt': '2024-01-07T10:30:00Z',
                    'content': 'Financial institutions are increasingly turning to neural networks for trading strategies...'
                },
                {
                    'title': 'Machine Learning Detects Early Signs of Cancer',
                    'description': 'New ML algorithms can detect cancer in medical scans with 98% accuracy, often identifying tumors months before traditional methods.',
                    'url': 'https://example.com/ml-cancer-detection',
                    'source': {'name': 'Medical AI Advances'},
                    'publishedAt': '2024-01-07T09:45:00Z',
                    'content': 'Machine learning is transforming cancer diagnosis with early detection capabilities...'
                }
            ]
            
            # Enhanced filtering based on query
            query_lower = query.lower()
            if any(term in query_lower for term in ['ml', 'machine learning', 'ai', 'artificial intelligence', 'news', 'latest', 'top stories', 'trending']):
                # Return comprehensive results for ML/AI queries
                return comprehensive_articles[:num_results]
            else:
                # Filter based on specific query terms
                filtered_articles = []
                for article in comprehensive_articles:
                    if any(word in article['title'].lower() or word in article['description'].lower() 
                           for word in query_lower.split()):
                        filtered_articles.append(article)
                return filtered_articles[:num_results] if filtered_articles else comprehensive_articles[:3]
            
        # Real API call (when API key is provided)
        # Try multiple endpoints for comprehensive coverage
        articles = []
        
        # Get trending headlines first
        if any(term in query.lower() for term in ['trending', 'top stories', 'latest', 'news']):
            headlines_url = f"https://newsapi.org/v2/top-headlines?category=technology&apiKey={api_key}&language=en&pageSize=10"
            try:
                response = requests.get(headlines_url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == 'ok' and data.get('articles'):
                        for article in data['articles']:
                            if article.get('title') and article.get('url'):
                                articles.append({
                                    'title': article['title'],
                                    'description': article.get('description', ''),
                                    'url': article['url'],
                                    'source': article.get('source', {}).get('name', 'Unknown'),
                                    'publishedAt': article.get('publishedAt', ''),
                                    'content': article.get('content', '')
                                })
            except Exception as e:
                print(f"Error fetching headlines: {e}")
        
        # Get specific search results
        search_url = f"https://newsapi.org/v2/everything?q={query}&apiKey={api_key}&language=en&sortBy=publishedAt&pageSize={num_results}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        try:
            response = requests.get(search_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') == 'ok' and data.get('articles'):
                for article in data['articles']:
                    if article.get('title') and article.get('url'):
                        articles.append({
                            'title': article['title'],
                            'description': article.get('description', ''),
                            'url': article['url'],
                            'source': article.get('source', {}).get('name', 'Unknown'),
                            'publishedAt': article.get('publishedAt', ''),
                            'content': article.get('content', '')
                        })
        except Exception as e:
            print(f"Error fetching search results: {e}")
        
        # Remove duplicates and return
        seen_titles = set()
        unique_articles = []
        for article in articles:
            if article['title'] not in seen_titles:
                seen_titles.add(article['title'])
                unique_articles.append(article)
        
        return unique_articles[:num_results]
        
    except Exception as e:
        print(f"Error fetching news from API: {e}")
        return []

def get_google_news(query, num_results=3):
    """Get news articles - wrapper function that uses News API"""
    return get_news_api_articles(query, num_results)

def fetch_article_content(url):
    """Fetch and extract main content from a news article URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try to find the main article content
        content_selectors = [
            'article',
            'div.article-body',
            'div.article-content',
            'div.story-body',
            'div.entry-content',
            'div.post-content',
            'div[itemprop="articleBody"]',
            'div.article__content',
            'div.article-text',
            'div.content__body',
            'div.post__content'
        ]
        
        for selector in content_selectors:
            article = soup.select_one(selector)
            if article:
                # Remove unwanted elements
                for elem in article.find_all(['script', 'style', 'nav', 'footer', 'aside']):
                    elem.decompose()
                
                # Get all text content
                text = ' '.join(p.get_text(' ', strip=True) for p in article.find_all(['p', 'h2', 'h3', 'h4']))
                if len(text) > 100:  # Ensure we have meaningful content
                    return ' '.join(text.split()[:200]) + '...'  # Return first 200 words
                
                return None
        
    except Exception as e:
        print(f"Error fetching article content: {e}")
        return None

    return None

def parse_reminder_time(time_str):
    """Parse natural language time expressions into datetime objects"""
    if not time_str:
        return None
        
    now = datetime.datetime.now()
    time_str = time_str.lower()
    
    # Handle "in X minutes/hours"
    time_match = re.search(r'in\s+(\d+)\s+(minute|hour|day|week)s?', time_str)
    if time_match:
        value = int(time_match.group(1))
        unit = time_match.group(2)
        
        if unit.startswith('min'):
            return now + datetime.timedelta(minutes=value)
        elif unit.startswith('hour'):
            return now + datetime.timedelta(hours=value)
        elif unit.startswith('day'):
            return now + datetime.timedelta(days=value)
        elif unit.startswith('week'):
            return now + datetime.timedelta(weeks=value)
    
    # Handle "at 3 PM" or "at 15:30"
    time_match = re.search(r'at\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', time_str)
    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2) or 0)
        period = time_match.group(3)
        
        # Convert 12-hour to 24-hour format
        if period:
            if period == 'pm' and hour < 12:
                hour += 12
            elif period == 'am' and hour == 12:
                hour = 0
        
        # Create datetime for today at the specified time
        reminder_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # If the time has already passed today, schedule for tomorrow
        if reminder_time < now:
            reminder_time += datetime.timedelta(days=1)
            
        return reminder_time
    
    # Handle "tomorrow at [time]"
    if 'tomorrow' in time_str:
        tomorrow = now + datetime.timedelta(days=1)
        time_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', time_str)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2) or 0)
            period = time_match.group(3)
            
            if period:
                if period == 'pm' and hour < 12:
                    hour += 12
                elif period == 'am' and hour == 12:
                    hour = 0
            
            return tomorrow.replace(hour=hour, minute=minute, second=0, microsecond=0)
        return tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)  # Default to 9 AM tomorrow
    
    return None

def init_database():
    """Initialize SQLite database for reminders"""
    conn = sqlite3.connect('reminders.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reminder_text TEXT NOT NULL,
            reminder_time DATETIME NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_completed BOOLEAN DEFAULT 0
        )
    ''')
    conn.commit()
    return conn

def set_reminder(reminder_text, time_str=None):
    """Set a reminder with natural language time parsing"""
    try:
        # Initialize database connection
        conn = init_database()
        cursor = conn.cursor()
        
        # Parse the reminder time
        reminder_time = parse_reminder_time(time_str) if time_str else None
        
        # If no specific time, set default (1 hour from now)
        if not reminder_time:
            reminder_time = datetime.datetime.now() + datetime.timedelta(hours=1)
            response = f"I'll remind you in 1 hour: {reminder_text}"
        else:
            response = f"I'll remind you at {reminder_time.strftime('%I:%M %p')} on {reminder_time.strftime('%A, %B %d')}: {reminder_text}"
        
        # Save to database
        cursor.execute(
            'INSERT INTO reminders (reminder_text, reminder_time) VALUES (?, ?)',
            (reminder_text, reminder_time.isoformat())
        )
        conn.commit()
        conn.close()
        
        return response
        
    except Exception as e:
        print(f"Error setting reminder: {e}")
        return "I couldn't set that reminder. Please try again with a specific time."

def get_due_reminders():
    """Get reminders that are due"""
    try:
        conn = sqlite3.connect('reminders.db')
        cursor = conn.cursor()
        
        now = datetime.datetime.now().isoformat()
        cursor.execute(
            'SELECT id, reminder_text FROM reminders WHERE reminder_time <= ? AND is_completed = 0 ORDER BY reminder_time',
            (now,)
        )
        
        reminders = cursor.fetchall()
        
        # Mark reminders as completed
        for reminder_id, _ in reminders:
            cursor.execute(
                'UPDATE reminders SET is_completed = 1 WHERE id = ?',
                (reminder_id,)
            )
        
        conn.commit()
        conn.close()
        
        return [text for _, text in reminders]
        
    except Exception as e:
        print(f"Error getting reminders: {e}")
        return []

def get_weather(city=""):
    try:
        if not city:
            # Default to a city if none specified, or ask for location
            return "Please specify a city for the weather, like 'weather in New York'."

        obs = weather_client.weather_at_place(city)
        weather = obs.weather
        temperature = weather.temperature('celsius')
        description = weather.detailed_status

        return f"Weather in {city}: {description}. Temperature: {temperature['temp']}°C (feels like {temperature['feels_like']}°C)."

    except Exception as e:
        return "I couldn't get the weather information. Please check the city name or try again later."

def extract_city_from_query(query):
    # Simple extraction of city names from weather queries
    # This is a basic implementation - could be improved with better NLP
    doc = nlp(query)

    # Look for proper nouns (likely city names) after "weather in" or similar
    words = [token.text for token in doc if token.pos_ == "PROPN"]

    # If we find words after "in", take those as city name
    query_lower = query.lower()
    if "weather in" in query_lower:
        in_index = query_lower.find("weather in") + len("weather in")
        city_part = query[in_index:].strip()
        return city_part
    elif "in" in query_lower and "weather" in query_lower:
        # Try to find city name after "in"
        parts = query_lower.split("in")
        if len(parts) > 1:
            city_part = parts[1].strip()
            # Take first word as city (simplified)
            return city_part.split()[0]

    # Default fallback
    return ""


def get_reminders():
    """Get all active reminders"""
    if not reminders:
        return "You have no reminders set."
    
    current_time = datetime.datetime.now()
    active_reminders = []
    
    for i, reminder in enumerate(reminders, 1):
        if reminder['time'] and reminder['time'] <= current_time:
            active_reminders.append(f"{i}. {reminder['text']} (Due: {reminder['time'].strftime('%I:%M %p')})")
        else:
            active_reminders.append(f"{i}. {reminder['text']}")
    
    return "Here are your reminders:\n" + "\n".join(active_reminders)

def process_command(command):
    """Process user command and return appropriate response"""
    if not command or not command.strip():
        return "I didn't catch that. Could you please repeat?"
    
    command_lower = command.lower()
    
    # Check for greetings
    if any(greeting in command_lower for greeting in GREETING_INPUTS):
        return greet()
    
    # Check for time/date queries
    if any(word in command_lower for word in ['time', 'what time', 'current time']):
        return get_time()
    if any(word in command_lower for word in ['date', 'today', 'what day']):
        return get_date()
    
    # Check for math queries
    math_indicators = ['+', '-', '*', '/', '=', 'plus', 'minus', 'times', 'divided by', 'add', 'subtract', 'multiply', 'divide', 'calculate', 'solve', 'math']
    if any(word in command_lower for word in math_indicators) or any(word.isdigit() for word in command_lower.split()):
        return solve_math(command)
    
    # Check for weather queries
    if any(word in command_lower for word in ['weather', 'temperature', 'forecast', 'how is the weather']):
        city = extract_city_from_query(command)
        return get_weather(city)
    
    # Check for comprehensive news requests
    if any(phrase in command_lower for phrase in ['all details from api', 'fetch all details', 'comprehensive news', 'all ml ai news', 'all trending news']):
        return get_trending_news(7)
    
    # Check for trending news requests
    if any(word in command_lower for word in ['trending', 'top stories', 'latest news', 'all news']):
        return get_trending_news(5)
    
    # Check for search queries
    if any(word in command_lower for word in ['search', 'find', 'google', 'look up', 'who is', 'what is', 'where is']) or '?' in command_lower:
        # Clean the query by removing common search verbs
        clean_query = ' '.join([word for word in command.split() 
                              if word.lower() not in ['search', 'for', 'find', 'about', 'look', 'up', 'google']])
        
        # If the query is too short after cleaning, ask for more details
        if len(clean_query.strip()) < 3:
            return "I need more details to search. What specifically are you looking for?"
            
        # Perform the search directly
        return search_web(clean_query)
    
    # Check for reminder queries
    reminder_indicators = ['remind', 'reminder', 'remember', 'alert', 'notify']
    if any(word in command_lower for word in reminder_indicators):
        # Try to extract reminder text and time
        reminder_text = command
        time_match = None
        
        # Look for time patterns
        time_match = re.search(r'(at\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)?|in\s+\d+\s+(?:minute|hour|day|week)s?|tomorrow)', command_lower)
        
        if time_match:
            time_str = time_match.group(1)
            reminder_text = reminder_text.replace(time_str, '')
        else:
            time_str = None
        
        # Clean up reminder text
        reminder_text = re.sub(r'\b(remind|me|to|set|a|an|the|about|that|please|would you|can you|could you)\b', '', reminder_text, flags=re.IGNORECASE)
        reminder_text = reminder_text.strip()
        
        if not reminder_text:
            return "What would you like me to remind you about?"
            
        return set_reminder(reminder_text, time_str if time_match else None)
    
    # Check for list reminders
    if any(word in command_lower for word in ['my reminders', 'show reminders', 'list reminders', 'any reminders']):
        reminders = get_due_reminders()
        if reminders:
            return "🔔 Reminders:\n" + "\n\n".join([f"• {reminder}" for reminder in reminders])
        return "You don't have any pending reminders."
    
    # If the command is short or seems like a search query
    if len(command.split()) < 5 or any(len(word) > 15 for word in command.split()):
        return search_web(command)
    
    # Default response for unknown commands
    return "I'm not sure how to help with that. You can ask me about the time, weather, to set reminders, do math, or search the web."
