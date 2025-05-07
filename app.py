from flask import Flask, request, jsonify, render_template
import os
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from textblob import TextBlob
import re
from urllib.parse import urlparse

app = Flask(__name__, static_folder=os.path.join('static'))

CORS(app)

# Ensure NLTK resources are downloaded (only need to do this once)
nltk.download('vader_lexicon')
nltk.download('punkt')  # for TextBlob sentence tokenization

def scrape_article(url):
    """
    Scrapes the headline and article text from a given URL.
    """
    try:
        print(f"Attempting to scrape: {url}")  #  Log the URL
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'}  #  A common User-Agent
        response = requests.get(url, headers=headers)
        response.raise_for_status()  #  Raise an exception for bad status codes
        print(f"Response status code: {response.status_code}")  #  Log status code
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract headline (prioritizing og:title, then title tag)
        headline = soup.find("meta", property="og:title")
        if headline:
            headline = headline["content"]
        else:
            headline = soup.find('title').text if soup.find('title') else ""

        # Extract article text (finding all paragraph elements)
        paragraphs = soup.find_all('p')
        article_text = ' '.join([p.text for p in paragraphs]) if paragraphs else ""

        print(f"Headline: {headline}")  #  Log headline
        print(f"Article text: {article_text[:100]}...")  #  Log first 100 chars of text

        return headline, article_text

    except requests.exceptions.RequestException as e:
        print(f"Error during scraping: {e}")  #  Log the exception
        return None, None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None, None


def analyze_sentiment(text):
    """
    Performs sentiment analysis on the given text.
    """
    analyzer = SentimentIntensityAnalyzer()
    vs = analyzer.polarity_scores(text)
    #  Simplified sentiment interpretation
    if vs['compound'] >= 0.05:
        return "Positive"
    elif vs['compound'] <= -0.05:
        return "Negative"
    else:
        return "Neutral"

def check_clickbait(headline):
    """
    Checks if a headline is clickbait-like.
    (Very basic clickbait detection)
    """
    clickbait_patterns = [
        r"You won't believe",
        r"Shocking",
        r"OMG",
        r"This changed everything",
        r"Top \d+ things"
    ]
    for pattern in clickbait_patterns:
        if re.search(pattern, headline, re.IGNORECASE):
            return True
    return False

def check_source_credibility(url):
    """
    Basic check against a list of unreliable sources.
    (This is a simplified example; a real-world implementation would be much more robust)
    """
    unreliable_sources = [
        "example.com",  # Replace with actual unreliable sources
        "another-fake-news.net"
    ]
    try:
        parsed_url = urlparse(url)
        source_domain = parsed_url.netloc
        for source in unreliable_sources:
            if source in source_domain:
                return "Unreliable"
        return "Likely Reliable"
    except:
        return "Source Credibility Unknown"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_news():
    """
    Flask route to analyze a news article.
    """

    url = request.json['url']
    headline, article_text = scrape_article(url)

    if headline and article_text:
        sentiment = analyze_sentiment(article_text)
        clickbait = check_clickbait(headline)
        source_credibility = check_source_credibility(url)

        result = {
            "url": url,
            "headline": headline,
            "article_text": article_text,
            "sentiment": sentiment,
            "clickbait": clickbait,
            "source_credibility": source_credibility,
            "message": "Article analyzed successfully"
        }
    else:
        result = {"url": url, "error": "Failed to scrape or analyze article"}

    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)    
    