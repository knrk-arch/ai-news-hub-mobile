import streamlit as st
from extractor import get_latest_ai_news

# ==========================================
# Mobile Optimized Configuration (V6)
# ==========================================
st.set_page_config(
    page_title="AI News Hub", 
    page_icon="📱", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for Ergonomic Mobile UI
st.markdown("""
<style>
    /* Reset Streamlit paddings for full screen bleed */
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
        padding-left: 0rem !important;
        padding-right: 0rem !important;
        max-width: 100% !important;
    }
    header { visibility: hidden; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }

    /* Free Scrolling Container (Removed annoying snap) */
    html, body, .stApp {
        background-color: #0d0d12;
        margin: 0;
        padding: 0;
        color: #ffffff;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        -webkit-overflow-scrolling: touch;
    }

    /* Fixed Top Tab Bar */
    .top-tab-bar {
        position: sticky;
        top: 0;
        z-index: 100;
        background: rgba(13, 13, 18, 0.85);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border-bottom: 1px solid rgba(255,255,255,0.1);
        padding: 12px 16px;
        display: flex;
        gap: 12px;
        overflow-x: auto;
        white-space: nowrap;
        scrollbar-width: none;
    }
    .top-tab-bar::-webkit-scrollbar {
        display: none;
    }
    
    .tab-item {
        color: rgba(255,255,255,0.6);
        background: rgba(255,255,255,0.05);
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 600;
        text-decoration: none;
        transition: all 0.2s;
        border: 1px solid transparent;
    }
    .tab-item.active {
        color: #ffffff;
        background: rgba(255,255,255,0.15);
        border: 1px solid rgba(255,255,255,0.3);
    }

    /* Article Card List */
    .feed-container {
        padding: 16px;
        display: flex;
        flex-direction: column;
        gap: 24px;
        padding-bottom: 80px;
    }

    .article-card {
        background: #181820;
        border-radius: 24px;
        padding: 24px;
        border: 1px solid rgba(255,255,255,0.05);
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }

    /* Dynamic gradient accents */
    .border-qiita { border-top: 4px solid #55c500; }
    .border-zenn { border-top: 4px solid #3ea8ff; }
    .border-google { border-top: 4px solid #ea4335; }
    .border-hatena { border-top: 4px solid #008fde; }
    .border-hacker { border-top: 4px solid #ff6600; }
    .border-techcrunch { border-top: 4px solid #00a562; }
    .border-gizmodo { border-top: 4px solid #ffffff; }

    /* Header info */
    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
    }

    .source-badge {
        font-size: 0.75rem;
        font-weight: 700;
        color: rgba(255, 255, 255, 0.5);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .time-badge {
        font-size: 0.75rem;
        color: rgba(255, 255, 255, 0.4);
    }

    /* Title Area (Smaller in V6) */
    .article-title {
        font-size: 1.2rem;
        font-weight: 700;
        line-height: 1.4;
        color: rgba(255, 255, 255, 0.85);
        text-decoration: none;
        display: block;
        margin-bottom: 16px;
    }
    .article-subtitle {
        font-size: 0.85rem;
        color: rgba(255, 255, 255, 0.4);
        margin-bottom: 16px;
        font-style: italic;
    }

    /* Summary Block (Larger and More Readable in V6) */
    .summary-text {
        font-size: 1.15rem;
        line-height: 1.7;
        color: #ffffff;
        font-weight: 400;
        margin-bottom: 24px;
        padding-left: 12px;
        border-left: 2px solid rgba(255,255,255,0.1);
    }

    .ai-label {
        color: #4facfe;
        font-size: 0.75rem;
        font-weight: 700;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 6px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Bottom Action */
    .read-btn {
        display: block;
        text-align: center;
        background: rgba(255,255,255,0.08);
        color: #ffffff;
        text-decoration: none;
        padding: 14px;
        border-radius: 14px;
        font-weight: 600;
        font-size: 0.95rem;
        transition: background 0.2s;
    }
    .read-btn:active {
        background: rgba(255,255,255,0.15);
    }
    
    /* Loading View */
    .loading-view {
        height: 100vh;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        background: #0d0d12;
        color: white;
    }
    
    .spinner {
        width: 40px;
        height: 40px;
        border: 4px solid rgba(255,255,255,0.1);
        border-left-color: #4facfe;
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin-bottom: 20px;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# Fetch Data
# ==========================================

if 'articles' not in st.session_state:
    st.session_state.articles = []
    
if not st.session_state.articles:
    st.markdown("""
        <div class="loading-view">
            <div class="spinner"></div>
            <h2>最新のAI & ガジェットニュースを収集中...</h2>
            <p style="color: #666;">※自動要約・翻訳を行っているため20秒ほどかかります</p>
        </div>
    """, unsafe_allow_html=True)
    st.session_state.articles = get_latest_ai_news()
    st.rerun()

# ==========================================
# Top Navigation & Filtering
# ==========================================

# Using query params for simple tab state without rerun loops
query_params = st.query_params
current_tab = query_params.get("tab", "all")

col1, col2, col3 = st.columns(3)

# Define categories
cats = {
    "all": "すべてのニュース",
    "ai": "AI・トレンド",
    "gadget": "ガジェット",
}

# Create top sticky tab bar HTML
tab_html = '<div class="top-tab-bar">'
for key, label in cats.items():
    active_class = "active" if current_tab == key else ""
    # Instead of actual links which trigger full reloads in streamlit, we use streamlit buttons styled as tabs
    # Since we can't easily style st.button to look exactly like a horizontal scorllable tab bar,
    # we'll build a custom HTML navigation that uses Streamlit's routing via URL parameters or we just use native columns.
    pass

# Workaround for Streamlit Tabs: Use standard pill buttons at the top
st.markdown('<div style="padding: 16px 16px 0 16px;">', unsafe_allow_html=True)
selected_tab = st.radio(
    "トピックフィルター",
    ["すべてのニュース", "AI・トレンド", "ガジェット"],
    horizontal=True,
    label_visibility="collapsed"
)
st.markdown('</div>', unsafe_allow_html=True)

# Filter logic
filtered_articles = []
for a in st.session_state.articles:
    src = a["source"]
    is_gadget = any(g in src for g in ["Gizmodo", "Engadget", "WIRED", "GIGAZINE", "ITmedia", "ASCII", "PC Watch"])
    
    if selected_tab == "ガジェット" and is_gadget:
        filtered_articles.append(a)
    elif selected_tab == "AI・トレンド" and not is_gadget:
        filtered_articles.append(a)
    elif selected_tab == "すべてのニュース":
        filtered_articles.append(a)


# ==========================================
# Render Ergonomic Cards
# ==========================================

html_cards = ['<div class="feed-container">']

for article in filtered_articles:
    src = article["source"]
    
    # Determine border accent
    border_class = "border-gizmodo"
    if "Qiita" in src: border_class = "border-qiita"
    elif "Zenn" in src: border_class = "border-zenn"
    elif "Google" in src: border_class = "border-google"
    elif "Hatena" in src: border_class = "border-hatena"
    elif "Hacker News" in src: border_class = "border-hacker"
    elif "TechCrunch" in src: border_class = "border-techcrunch"

    # Title & Subtitle (Original English)
    title_html = ""
    if article.get("is_foreign", False) and "title_ja" in article:
        title_html = f'<a href="{article["link"]}" target="_blank" class="article-title">{article["title_ja"]}</a>'
        title_html += f'<div class="article-subtitle">{article["title"]}</div>'
    else:
        title_html = f'<a href="{article["link"]}" target="_blank" class="article-title">{article["title"]}</a>'

    # Summary Box
    summary_html = ""
    if article.get("is_foreign", False) and "summary_ja" in article:
        summary_html = f"""
<div class="ai-label">
<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
AI 翻訳要約
</div>
{article["summary_ja"]}
"""
    else:
        desc = article["description"]
        if len(desc) > 180: desc = desc[:177] + "..."
        summary_html = desc

    # Construct the entire card safely without indentation
    card_html = f"""
<div class="article-card {border_class}">
<div class="card-header">
<div class="source-badge">{src}</div>
<div class="time-badge">{article["published_at"]}</div>
</div>

{title_html}

<div class="summary-text">
{summary_html}
</div>

<a href="{article["link"]}" target="_blank" class="read-btn">
元の記事を読む
</a>
</div>
"""
    
    html_cards.append(card_html)

html_cards.append('</div>')

# Output
st.markdown("".join(html_cards), unsafe_allow_html=True)
