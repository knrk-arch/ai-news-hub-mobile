import feedparser
from datetime import datetime
import time
import trafilatura
from deep_translator import GoogleTranslator
from concurrent.futures import ThreadPoolExecutor, as_completed
import nltk
from nltk.corpus import stopwords
import string
import json
import os
import hashlib
from bs4 import BeautifulSoup
from dateutil import parser as dateutil_parser
import pytz

# Setup NLTK (Download silently)
for item in ['punkt', 'punkt_tab', 'stopwords']:
    try:
        if item == 'stopwords':
            nltk.data.find('corpora/stopwords')
        else:
            nltk.data.find(f'tokenizers/{item}')
    except LookupError:
        nltk.download(item, quiet=True)

# 5 Core Categories mapping to their respective RSS sources
CATEGORIES = {
    "AI・テクノロジートレンド": [
        {"url": "https://hnrss.org/newest?q=AI+OR+LLM+OR+ChatGPT&points=100", "name": "Hacker News"},
        {"url": "https://techcrunch.com/category/artificial-intelligence/feed/", "name": "TechCrunch"},
        {"url": "https://zenn.dev/topics/ai/feed", "name": "Zenn"}
    ],
    "ガジェット・ハードウェア": [
        {"url": "https://www.gizmodo.jp/index.xml", "name": "Gizmodo Japan"},
        {"url": "https://hnrss.org/newest?q=Hardware+OR+Gadget&points=50", "name": "Hacker News Hardware"},
        {"url": "https://japanese.engadget.com/rss.xml", "name": "Engadget"}
    ],
    "ビジネス・経済": [
        {"url": "https://hnrss.org/newest?q=Business+OR+Market+OR+Economy&points=100", "name": "HN Business"},
        {"url": "https://news.google.com/rss/search?q=%E3%83%86%E3%82%AF%E3%83%8E%E3%83%AD%E3%82%B8%E3%83%BC+%E4%BA%8B%E6%A5%AD&hl=ja&gl=JP&ceid=JP:ja", "name": "Google News Biz"}
    ],
    "ライフハック・仕事術": [
        {"url": "https://b.hatena.ne.jp/q/%E3%83%A9%E3%82%A4%E3%83%95%E3%83%8F%E3%83%83%E3%82%AF?sort=recent&safe=on&mode=rss", "name": "Hatena Lifehack"},
        {"url": "https://lifehacker.com/feed/rss", "name": "Lifehacker"}
    ],
    "サイエンス・未来予測": [
        {"url": "https://hnrss.org/newest?q=Science+OR+Space+OR+Physics&points=100", "name": "HN Science"},
        {"url": "https://wired.jp/rss/index.xml", "name": "WIRED Japan"}
    ]
}

def parse_date(date_string):
    if not date_string:
        return datetime.now()
    try:
        parsed = feedparser._parse_date(date_string)
        if parsed:
            return datetime.fromtimestamp(time.mktime(parsed))
    except Exception: pass
        
    try:
        dt = dateutil_parser.parse(date_string)
        if dt.tzinfo:
            dt = dt.astimezone(pytz.utc).replace(tzinfo=None)
        return dt
    except Exception: pass
    return datetime.now()

def extract_tags(text, num_tags=3):
    """
    Extracts 3-5 core noun keywords from the text, ignoring stopwords.
    Translates them to Japanese if necessary.
    """
    if not text or len(text) < 10:
        return []
        
    # Standardize
    translator = GoogleTranslator(source='auto', target='ja')
    
    # Try to extract English words if it's english text
    is_english = len([char for char in text[:500] if ord(char) < 128]) / min(500, len(text)) > 0.8
    lang = 'english' if is_english else None
    
    if lang == 'english':
        tokens = nltk.word_tokenize(text)
        stop_words = set(stopwords.words('english') + list(string.punctuation) + ['The', 'A', 'An', 'It', 'This', 'That'])
        
        # Focus on capitalized words (proper nouns/products) or long words
        candidates = [w for w in tokens if w not in stop_words and len(w) > 3 and not w.isnumeric()]
        
        # Super simple frequency distribution to find the 'core' themes
        freq = nltk.FreqDist(candidates)
        top_words = [word for word, count in freq.most_common(num_tags)]
        
        tags_ja = []
        for w in top_words:
            try:
                tags_ja.append(translator.translate(w))
            except:
                tags_ja.append(w)
        return tags_ja
    else:
        # For Japanese text, since we don't have MeCab installed, we'll try a rough heuristic:
        # Extract alphanumeric English words from the Japanese text (e.g. "Apple", "GPT-4")
        tokens = nltk.word_tokenize(text)
        english_ish = [w for w in tokens if w.isalnum() and len(w) > 2 and any(c.isalpha() for c in w) and all(ord(c) < 128 for c in w)]
        freq = nltk.FreqDist(english_ish)
        return [word for word, count in freq.most_common(num_tags)]

def process_article(entry, source_name, cat):
    title = entry.get('title', 'No Title')
    link = entry.url if "url" in entry else entry.get('link', '')
    
    published = entry.get('published', entry.get('pubDate', entry.get('updated', entry.get('dc:date', entry.get('date', '')))))
    pub_date = parse_date(published)
    
    # ID Generation
    uid = hashlib.md5(link.encode('utf-8')).hexdigest()

    # Base translation
    translator = GoogleTranslator(source='auto', target='ja')
    try:
        title_ja = translator.translate(title) if len(title) > 0 and ord(title[0]) < 128 else title
    except:
        title_ja = title
        
    # Download content via trafilatura for the core sentence
    downloaded = trafilatura.fetch_url(link)
    core_sentence = "内容を抽出できませんでした。リンク元をご確認ください。"
    tags = []
    read_time = 1
    
    if downloaded:
        text = trafilatura.extract(downloaded)
        if text:
            # Idea C: Basic cleanup
            clean_lines = [line.strip() for line in text.split('\n') if len(line.strip()) > 15 and not any(nw in line.lower() for nw in ['cookie', 'subscribe', 'log in', 'sign up', 'read more'])]
            if clean_lines:
                clean_text = ' '.join(clean_lines)
                
                # Estimate read time based on total extracted text
                # average reading speed in Japanese is around 400 chars/minute
                read_time = max(1, round(len(clean_text) / 400))
                
                # Lead-1 approach (Idea D variation: Take the first substantial sentence)
                sentences = nltk.sent_tokenize(clean_text)
                if sentences:
                    lead_sentence = sentences[0]
                    # Translate if english
                    is_english = len([char for char in lead_sentence if ord(char) < 128]) / len(lead_sentence) > 0.8
                    if is_english:
                        try:
                            core_sentence = translator.translate(lead_sentence)
                        except:
                            core_sentence = lead_sentence
                    else:
                        core_sentence = lead_sentence
            
            # Extract tags from the cleaned text
            tags = extract_tags(text, 3)
            
    # Fallback to description if trafilatura fails entirely and we have an RSS summary
    if core_sentence.startswith("内容を") and entry.get('summary'):
        summary = BeautifulSoup(entry.summary, "html.parser").get_text(separator=' ', strip=True)
        if summary:
            sentences = nltk.sent_tokenize(summary)
            if sentences:
                s = sentences[0]
                try:
                    core_sentence = translator.translate(s) if ord(s[0]) < 128 else s
                except:
                    core_sentence = s

    # Ensure tags isn't completely empty for UI aesthetic
    if not tags:
        # Fallback to category tag or source name
        tags = [cat.split('・')[0], source_name.split(' ')[0]]
        
    # Ensure translated core sentence is not overwhelmingly long
    if len(core_sentence) > 120:
        core_sentence = core_sentence[:118] + "..."

    # Create pseudo-insight using lightweight logic based on tags and category
    import random
    tag1 = tags[0][:8] if tags else cat.split('・')[0] # Limit tag length to fit insight smoothly
    templates = {
        "AI・テクノロジートレンド": [f"{tag1}の活用がさらに拡大", f"{tag1}による業務の高速化", f"次世代{tag1}への移行加速"],
        "ガジェット・ハードウェア": [f"{tag1}による生活の質向上", f"新しい{tag1}体験が普及", f"{tag1}のエコシステム強化"],
        "ビジネス・経済": [f"{tag1}市場の競争が激化", f"{tag1}関連の投資が加速", f"{tag1}が業界標準を変える"],
        "ライフハック・仕事術": [f"{tag1}の仕組み化で時短", f"{tag1}の活用で生産性UP", f"新しい{tag1}習慣の定着"],
        "サイエンス・未来予測": [f"{tag1}のブレイクスルー", f"{tag1}の新常識が到来", f"{tag1}の可能性が拡大"]
    }
    insight_text = random.choice(templates.get(cat, [f"{tag1}の新たな可能性が開拓"]))
    insight = f"💡 影響: {insight_text}"

    return {
        "id": uid,
        "category": cat,
        "title_ja": title_ja,
        "tags": tags,
        "insight": insight,
        "core_sentence": core_sentence,
        "source": source_name,
        "read_time_min": read_time,
        "url": link,
        "timestamp": pub_date.timestamp()
    }

def fetch_category(cat, feeds):
    all_cat_articles = []
    
    for feed_info in feeds:
        try:
            feed = feedparser.parse(feed_info["url"])
            if feed.entries:
                # We pull up to 10 candidates per feed
                for entry in feed.entries[:10]:
                    all_cat_articles.append((entry, feed_info["name"]))
        except Exception as e:
            print(f"Error fetching {feed_info['name']}: {e}")
            
    # Sort candidates by date, newest first
    def get_ts(item):
        published = item[0].get('published', item[0].get('pubDate', item[0].get('updated', item[0].get('dc:date', ''))))
        return parse_date(published).timestamp()
        
    all_cat_articles.sort(key=get_ts, reverse=True)
    
    # We only process the Absolute Top 5 candidates per category
    top_candidates = all_cat_articles[:5]
    
    processed = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(process_article, item[0], item[1], cat) for item in top_candidates]
        for f in as_completed(futures):
            res = f.result()
            if res:
                processed.append(res)
                
    # Re-sort to maintain chronological order in the top 5
    processed.sort(key=lambda x: x["timestamp"], reverse=True)
    return processed

def run_curation():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting Zero-Load Generation...") # Generating zero-load data
    
    final_output = []
    
    with ThreadPoolExecutor(max_workers=len(CATEGORIES)) as cat_executor:
        future_to_cat = {cat_executor.submit(fetch_category, cat, feeds): cat for cat, feeds in CATEGORIES.items()}
        for future in as_completed(future_to_cat):
            cat_name = future_to_cat[future]
            try:
                res = future.result()
                final_output.extend(res)
                print(f"   [DONE] {cat_name}: {len(res)} articles generated.")
            except Exception as e:
                print(f"   [ERROR] Category {cat_name} failed: {e}")
                
    # Sort global output
    final_output.sort(key=lambda x: x["timestamp"], reverse=True)
    
    # Save to JSON
    os.makedirs("data", exist_ok=True)
    output_path = os.path.join("data", "daily_curation.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_output, f, ensure_ascii=False, indent=4)
        
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Curation complete! Saved {len(final_output)} articles to {output_path}.")

if __name__ == "__main__":
    run_curation()
