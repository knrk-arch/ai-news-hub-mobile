import feedparser
from datetime import datetime
import time
import trafilatura
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from deep_translator import GoogleTranslator
from concurrent.futures import ThreadPoolExecutor, as_completed

def parse_date(date_string):
    try:
        parsed = feedparser._parse_date(date_string)
        if parsed:
            return datetime.fromtimestamp(time.mktime(parsed))
    except Exception:
        pass
    return datetime.now()

def fetch_rss_feed(url, source_name):
    articles = []
    try:
        feed = feedparser.parse(url)
        # To make auto-summarization faster, we limit the foreign sources slightly more
        limit = 10 if source_name in ["Hacker News", "TechCrunch"] else 15
        for entry in feed.entries[:limit]:
            title = entry.get('title', 'No Title')
            link = entry.get('link', '')
            published = entry.get('published', entry.get('updated', ''))
            
            pub_date = parse_date(published)
            
            summary = entry.get('summary', '')
            if len(summary) > 200:
                summary = summary[:200] + '...'
                
            if source_name == "Hacker News" and "url" in entry:
                link = entry.url
                
            articles.append({
                "title": title,
                "link": link,
                "published_at": pub_date.strftime("%Y/%m/%d %H:%M"),
                "timestamp": pub_date.timestamp(),
                "source": source_name,
                "description": summary,
                "is_foreign": source_name in ["Hacker News", "TechCrunch"]
            })
    except Exception as e:
        print(f"Error fetching {source_name}: {e}")
        
    return articles

def summarize_and_translate(url, sentences_count=3):
    try:
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return "※URLから本文を取得できませんでした。"
        
        text = trafilatura.extract(downloaded)
        if not text or len(text) < 100:
            return "※本文が短すぎる、または構造の問題により文章を抽出できませんでした。"

        is_english = len([char for char in text[:500] if ord(char) < 128]) / min(500, len(text)) > 0.8
        lang = "english" if is_english else "japanese"
        
        parser = PlaintextParser.from_string(text, Tokenizer(lang))
        summarizer = LsaSummarizer()
        summary_sentences = summarizer(parser.document, sentences_count)
        summary_text = " ".join([str(sentence) for sentence in summary_sentences])
        
        if is_english:
            translator = GoogleTranslator(source='auto', target='ja')
            summary_text = translator.translate(summary_text)

        return summary_text
    except Exception as e:
        return f"※要約の生成に失敗しました: {str(e)}"

def process_foreign_article(article):
    # Translate original title to Japanese
    try:
        translator = GoogleTranslator(source='auto', target='ja')
        article["title_ja"] = translator.translate(article["title"])
    except:
        article["title_ja"] = article["title"]
        
    # Auto summarize and translate body content
    article["summary_ja"] = summarize_and_translate(article["link"])

def get_latest_ai_news():
    feeds = [
        {"url": "https://qiita.com/tags/AI/feed", "name": "Qiita (AI)"},
        {"url": "https://qiita.com/tags/ChatGPT/feed", "name": "Qiita (ChatGPT)"},
        {"url": "https://zenn.dev/topics/ai/feed", "name": "Zenn (AI)"},
        {"url": "https://news.google.com/rss/search?q=AI+%E6%B4%BB%E7%94%A8+%E4%BA%8B%E4%BE%8B&hl=ja&gl=JP&ceid=JP:ja", "name": "Google News (AI 活用事例)"},
        {"url": "https://b.hatena.ne.jp/q/AI%20%E6%B4%BB%E7%94%A8?sort=recent&safe=on&mode=rss", "name": "Hatena Bookmark (AI)"},
        {"url": "https://hnrss.org/newest?q=AI+OR+LLM+OR+ChatGPT&points=50", "name": "Hacker News"},
        {"url": "https://techcrunch.com/category/artificial-intelligence/feed/", "name": "TechCrunch"},
        # 新しいガジェット系ニュースサイトを追加
        {"url": "https://www.gizmodo.jp/index.xml", "name": "Gizmodo Japan"},
        {"url": "https://japanese.engadget.com/rss.xml", "name": "Engadget (Archive)"},
        {"url": "https://wired.jp/rss/index.xml", "name": "WIRED Japan"}
    ]
    
    all_articles = []
    # 複数フィードの取得も並列化して速度を上げる
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_feed = {executor.submit(fetch_rss_feed, feed["url"], feed["name"]): feed for feed in feeds}
        for future in as_completed(future_to_feed):
            all_articles.extend(future.result())
            
    all_articles.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
    
    seen_links = set()
    unique_articles = []
    # 記事が多すぎると要約が遅くなるため、スマホ版は最新60件に絞る
    for article in all_articles:
        if article["link"] not in seen_links:
            seen_links.add(article["link"])
            unique_articles.append(article)
            
    unique_articles = unique_articles[:60]
            
    # Process foreign articles automatically in parallel (Translation + Summary)
    foreign_articles = [a for a in unique_articles if a.get("is_foreign")]
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(process_foreign_article, a) for a in foreign_articles]
        for f in as_completed(futures):
            pass
            
    return unique_articles
