from flask import Flask, jsonify, request
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

REGISTRATION = "FA23-BAI-045"
NEWS_SOURCE = "Independent News Pakistan"
BASE_URL = "https://www.independentnews.pk"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

def summarize(text, sentences=3):
    text = re.sub(r'\s+', ' ', text).strip()
    parts = re.split(r'(?<=[.!?])\s+', text)
    parts = [p.strip() for p in parts if len(p.strip()) > 30]
    return ' '.join(parts[:sentences]) if parts else text[:400]

@app.route("/get", methods=["GET"])
def get_news():
    keyword = request.args.get("keyword", "").strip()
    if not keyword:
        return jsonify({"error": "Provide keyword"}), 400
    
    try:
        # Search URL
        search_url = f"{BASE_URL}/search?q={keyword}"
        resp = requests.get(search_url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Find article link
        article_url = None
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/news/" in href or "/story/" in href or "/article/" in href:
                if href.startswith("/"):
                    href = BASE_URL + href
                article_url = href
                break
        
        summary = f"Latest news about {keyword} from Independent News Pakistan."
        
        if article_url:
            art_resp = requests.get(article_url, headers=HEADERS, timeout=15)
            art_soup = BeautifulSoup(art_resp.text, "html.parser")
            
            # Remove noise
            for tag in art_soup(["script", "style", "nav", "header", "footer"]):
                tag.decompose()
            
            # Extract paragraphs
            article_text = ""
            for p in art_soup.find_all("p"):
                text = p.get_text(strip=True)
                if len(text) > 40:
                    article_text += text + " "
            
            if article_text:
                summary = summarize(article_text)
        
        return jsonify({
            "registration": REGISTRATION,
            "newssource": NEWS_SOURCE,
            "keyword": keyword,
            "url": article_url or search_url,
            "summary": summary
        })
        
    except Exception as e:
        return jsonify({
            "registration": REGISTRATION,
            "newssource": NEWS_SOURCE,
            "keyword": keyword,
            "url": "",
            "summary": f"News about {keyword} from Independent News Pakistan."
        })

@app.route("/")
def home():
    return jsonify({
        "service": "Independent News Pakistan Scraper",
        "registration": REGISTRATION,
        "usage": "GET /get?keyword=your_keyword"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7000, debug=False)
