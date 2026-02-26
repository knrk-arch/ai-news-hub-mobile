import streamlit as st
from extractor import get_latest_ai_news

# ==========================================
# Mobile Optimized Configuration
# ==========================================
st.set_page_config(
    page_title="AI News Swipe", 
    page_icon="📱", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for TikTok/Reels style swipe UI
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

    /* Snap Scrolling Container */
    html, body, .stApp {
        scroll-snap-type: y mandatory;
        overflow-y: scroll;
        scroll-behavior: smooth;
        background-color: #000;
        margin: 0;
        padding: 0;
        -webkit-overflow-scrolling: touch;
    }

    /* Individual Swipe Card */
    .swipe-card {
        height: 100vh;
        width: 100vw;
        scroll-snap-align: start;
        position: relative;
        display: flex;
        flex-direction: column;
        color: #ffffff;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        box-sizing: border-box;
        overflow: hidden;
    }

    /* Dynamic gradients based on source (simulated dark mode) */
    .bg-qiita { background: linear-gradient(145deg, #112211 0%, #000000 100%); }
    .bg-zenn { background: linear-gradient(145deg, #001122 0%, #000000 100%); }
    .bg-google { background: linear-gradient(145deg, #220505 0%, #000000 100%); }
    .bg-hatena { background: linear-gradient(145deg, #001828 0%, #000000 100%); }
    .bg-hacker { background: linear-gradient(145deg, #331500 0%, #000000 100%); }
    .bg-techcrunch { background: linear-gradient(145deg, #002211 0%, #000000 100%); }
    .bg-gizmodo { background: linear-gradient(145deg, #222222 0%, #000000 100%); }
    .bg-default { background: linear-gradient(145deg, #1a1a2e 0%, #000000 100%); }

    .content-wrapper {
        z-index: 2;
        display: flex;
        flex-direction: column;
        height: 100%;
        padding: 60px 24px 40px 24px;
        justify-content: space-between;
    }

    /* Header info */
    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
    }

    .source-badge {
        background: rgba(255, 255, 255, 0.15);
        backdrop-filter: blur(5px);
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }

    .time-badge {
        font-size: 0.8rem;
        color: rgba(255, 255, 255, 0.6);
    }

    /* Title Area */
    .title-area {
        margin-top: auto;
        margin-bottom: 20px;
    }

    .article-title {
        font-size: 2rem;
        font-weight: 800;
        line-height: 1.25;
        color: #ffffff;
        text-decoration: none;
        display: block;
        text-shadow: 0 2px 10px rgba(0,0,0,0.5);
        margin-bottom: 8px;
    }
    
    .article-subtitle {
        font-size: 1rem;
        color: rgba(255, 255, 255, 0.7);
        margin-bottom: 12px;
        font-style: italic;
    }

    /* Summary Block */
    .summary-glass {
        background: rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 18px;
        font-size: 1.05rem;
        line-height: 1.5;
        color: rgba(255, 255, 255, 0.95);
        max-height: 40vh;
        overflow-y: auto;
        margin-bottom: 20px;
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
        display: flex;
        justify-content: center;
        align-items: center;
        background: #ffffff;
        color: #000000;
        text-decoration: none;
        padding: 16px;
        border-radius: 30px;
        font-weight: 700;
        font-size: 1.1rem;
        margin-bottom: 15px;
        transition: transform 0.2s;
    }
    .read-btn:active {
        transform: scale(0.96);
    }

    .swipe-instruction {
        text-align: center;
        font-size: 0.75rem;
        color: rgba(255,255,255,0.4);
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 4px;
        animation: subtle-bounce 2s infinite ease-in-out;
    }

    @keyframes subtle-bounce {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-6px); }
    }
    
    /* Loading View */
    .loading-view {
        height: 100vh;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        background: #000;
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
# Render Swipe Cards
# ==========================================

html_cards = []

for idx, article in enumerate(st.session_state.articles):
    src = article["source"]
    
    # Determine background class
    bg_class = "bg-default"
    if "Qiita" in src: bg_class = "bg-qiita"
    elif "Zenn" in src: bg_class = "bg-zenn"
    elif "Google" in src: bg_class = "bg-google"
    elif "Hatena" in src: bg_class = "bg-hatena"
    elif "Hacker News" in src: bg_class = "bg-hacker"
    elif "TechCrunch" in src: bg_class = "bg-techcrunch"
    elif "Gizmodo" in src or "Engadget" in src or "WIRED" in src: bg_class = "bg-gizmodo"

    card_html = f'<div class="swipe-card {bg_class}"><div class="content-wrapper">'
    
    # Header: Source & Time
    card_html += f"""
<div class="card-header">
<div class="source-badge">{src}</div>
<div class="time-badge">{article["published_at"]}</div>
</div>
"""
    
    # Title & Subtitle (Original English)
    card_html += '<div class="title-area">'
    if article.get("is_foreign", False) and "title_ja" in article:
        card_html += f'<a href="{article["link"]}" target="_blank" class="article-title">{article["title_ja"]}</a>'
        card_html += f'<div class="article-subtitle">{article["title"]}</div>'
    else:
        card_html += f'<a href="{article["link"]}" target="_blank" class="article-title">{article["title"]}</a>'
    card_html += '</div>'
    
    # Summary Box
    card_html += '<div class="summary-glass">'
    if article.get("is_foreign", False) and "summary_ja" in article:
        card_html += """
<div class="ai-label">
<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
AI 翻訳要約
</div>
"""
        card_html += article["summary_ja"]
    else:
        # For domestic sites, show the first 150 chars of description clearly
        desc = article["description"]
        if len(desc) > 150: desc = desc[:147] + "..."
        card_html += desc
    card_html += '</div>'
    
    # Bottom buttons
    card_html += f"""
<a href="{article["link"]}" target="_blank" class="read-btn">
記事をブラウザで開く
</a>
"""
    
    # Swipe Hint (Show on all but very last card)
    if idx < len(st.session_state.articles) - 1:
        card_html += """
<div class="swipe-instruction">
<span>上にスワイプして次のニュース</span>
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 19V5M5 12l7-7 7 7"/></svg>
</div>
"""
        
    card_html += '</div></div>'
    html_cards.append(card_html)

# Inject all cards into Streamlit at once
st.markdown("".join(html_cards), unsafe_allow_html=True)
