import streamlit as st
import json
import hashlib
import os
import streamlit.components.v1 as components

# ==========================================
# Native App Engine Configuration (V8)
# bypasses Streamlit UI limitations entirely
# ==========================================
st.set_page_config(
    page_title="AI & Gadget News Hub", 
    page_icon="📱", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

if 'articles' not in st.session_state:
    st.session_state.articles = []
    
# ZERO-LOAD: Instantly load from pre-compiled JSON instead of web scraping
# Hybrid Cloud Approach: Generate it if it doesn't exist yet (e.g., Streamlit Cloud Boot)
json_path = os.path.join("data", "daily_curation.json")

if not os.path.exists(json_path):
    st.markdown("""
        <div style="height: 100vh; display: flex; flex-direction: column; justify-content: center; align-items: center; background: #0d1117; color: white; font-family: sans-serif; position: fixed; top: 0; left: 0; width: 100vw; z-index: 999;">
            <div style="width: 48px; height: 48px; border: 4px solid rgba(255,255,255,0.05); border-left-color: #58a6ff; border-radius: 50%; animation: spin 1s cubic-bezier(0.5, 0, 0.5, 1) infinite; margin-bottom: 24px;"></div>
            <style>@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }</style>
            <h3 style="font-weight:600; margin-bottom: 12px; font-size: 1.3rem;">Initializing Curation Engine...</h3>
            <p style="color: #8b949e; font-size: 0.95rem; margin-bottom: 24px; text-align: center; max-width: 80%;">クラウドサーバーの初期化、または本日初のアクセスです。<br>最新のグローバルニュースをAIが厳選・翻訳しています（初回のみ約1〜2分かかります）</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Run the heavy generation live just this once
    try:
        from generate_curation import run_curation
        run_curation()
        # After success, we force a rerun so it loads perfectly via the standard JSON path
        st.rerun()
    except Exception as e:
        st.error(f"Failed to generate curation: {e}")
        st.stop()

# Load the JSON normally (0.1s Zero-Load state)
try:
    with open(json_path, 'r', encoding='utf-8') as f:
        st.session_state.articles = json.load(f)
except Exception as e:
    st.error(f"データの読み込みに失敗しました: {e}")
    st.stop()

# ---------------------------------------------------------
# UI Overhaul Hack:
# Make the Streamlit HTML Custom Component fullscreen
# This completely hides Streamlit's native layout engine
# ---------------------------------------------------------
st.markdown("""
<style>
    /* Hide Streamlit completely */
    header {visibility: hidden !important;}
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    .block-container {
        padding: 0 !important;
        margin: 0 !important;
        max-width: 100% !important;
    }
    .stApp {
        background-color: #0d1117;
    }
    
    /* Force any iframe (our frontend component) to take the entire viewport */
    iframe {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        width: 100vw !important;
        height: 100vh !important;
        z-index: 999999 !important;
        border: none !important;
    }
</style>
""", unsafe_allow_html=True)

# Serialize data for JS injection
# Need to replace some html characters to safely put in script tag
articles_json = json.dumps(st.session_state.articles).replace("</", "<\\/")

# ==========================================
# The Embedded Frontend App (Tailwind CSS + Vanilla JS)
# ==========================================
html_template = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>AI News Hub</title>
    <!-- Use Tailwind CSS for rapid styling -->
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        body {{
            font-family: 'Inter', -apple-system, sans-serif;
            background-color: #0d1117; /* GitHub Dark style background */
            color: #c9d1d9;
            margin: 0;
            padding: 0;
            -webkit-tap-highlight-color: transparent;
        }}
        
        /* Hide scrollbar for Tabs horizontally */
        .no-scrollbar::-webkit-scrollbar {{
            display: none;
        }}
        .no-scrollbar {{
            -ms-overflow-style: none;
            scrollbar-width: none;
        }}
        
        /* Glassmorphism Header */
        .glass-header {{
            background: rgba(13, 17, 23, 0.85);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-bottom: 1px solid rgba(255,255,255,0.08);
        }}
        
        /* Smooth interactions */
        .card-anim {{
            transition: transform 0.2s cubic-bezier(0.2, 0.8, 0.2, 1), box-shadow 0.2s;
        }}
        .card-anim:active {{
            transform: scale(0.98);
            background-color: #1c2128;
        }}
        
        .line-clamp-3 {{
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;  
            overflow: hidden;
        }}
    </style>
</head>
<body class="overflow-x-hidden antialiased flex flex-col h-screen">

    <!-- Sticky Header Area -->
    <header class="glass-header sticky top-0 z-50 px-4 py-3 flex flex-col gap-3 shadow-md">
        <!-- Top row: Title and Search -->
        <div class="flex items-center justify-between gap-3 pt-1">
            <h1 class="text-xl font-bold text-white whitespace-nowrap tracking-tight">AINews Hub</h1>
            <div class="relative w-full max-w-[220px]">
                <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <svg class="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                </div>
                <input type="text" id="searchInput" placeholder="記事を検索..." 
                       class="block w-full pl-9 pr-3 py-1.5 border border-gray-700 rounded-full leading-5 bg-[#161b22] text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:bg-[#1f242c] focus:border-blue-500 transition duration-150 ease-in-out">
            </div>
        </div>
        
        <!-- Bottom row: Horizontal Scrollable Tabs matching the 5 strict categories -->
        <nav class="flex space-x-2 overflow-x-auto no-scrollbar pb-1" id="tabContainer">
            <button onclick="changeTab('all')" class="tab-btn px-4 py-1.5 rounded-full text-[0.85rem] font-medium whitespace-nowrap bg-blue-500/20 text-blue-400 border border-blue-500/30 transition-colors" data-tab="all">すべて</button>
            <button onclick="changeTab('AI・テクノロジートレンド')" class="tab-btn px-4 py-1.5 rounded-full text-[0.85rem] font-medium whitespace-nowrap bg-white/5 text-gray-400 border border-transparent transition-colors shadow-sm" data-tab="AI・テクノロジートレンド">AI・トレンド</button>
            <button onclick="changeTab('ガジェット・ハードウェア')" class="tab-btn px-4 py-1.5 rounded-full text-[0.85rem] font-medium whitespace-nowrap bg-white/5 text-gray-400 border border-transparent transition-colors shadow-sm" data-tab="ガジェット・ハードウェア">ガジェット</button>
            <button onclick="changeTab('ビジネス・経済')" class="tab-btn px-4 py-1.5 rounded-full text-[0.85rem] font-medium whitespace-nowrap bg-white/5 text-gray-400 border border-transparent transition-colors shadow-sm" data-tab="ビジネス・経済">ビジネス・経済</button>
            <button onclick="changeTab('ライフハック・仕事術')" class="tab-btn px-4 py-1.5 rounded-full text-[0.85rem] font-medium whitespace-nowrap bg-white/5 text-gray-400 border border-transparent transition-colors shadow-sm" data-tab="ライフハック・仕事術">ライフハック</button>
            <button onclick="changeTab('サイエンス・未来予測')" class="tab-btn px-4 py-1.5 rounded-full text-[0.85rem] font-medium whitespace-nowrap bg-white/5 text-gray-400 border border-transparent transition-colors shadow-sm" data-tab="サイエンス・未来予測">サイエンス</button>
            <button onclick="changeTab('saved')" class="tab-btn px-4 py-1.5 rounded-full text-[0.85rem] font-medium whitespace-nowrap bg-white/5 text-gray-400 border border-transparent transition-colors shadow-sm flex items-center gap-1.5" data-tab="saved">
                <svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20"><path d="M5 4a2 2 0 012-2h6a2 2 0 012 2v14l-5-2.5L5 18V4z"></path></svg>
                保存済み
            </button>
        </nav>
        
        <div id="statsBanner" class="text-xs text-gray-400 text-center font-medium mt-1">表示中: 0件</div>
    </header>

    <!-- Main Content Area where infinite scroll happens natively -->
    <main class="flex-1 overflow-y-auto w-full" id="scrollArea">
        <div class="px-4 py-4 pb-24 flex flex-col gap-4" id="feedContainer">
            <!-- JavaScript dynamically injects cards here -->
        </div>
    </main>

    <!-- Floating Action Button for Scroll to Top -->
    <button id="scrollTopBtn" onclick="scrollToTop()" class="fixed bottom-6 right-6 w-12 h-12 bg-[#58a6ff] hover:bg-blue-500 text-white rounded-full shadow-xl shadow-blue-900/30 flex items-center justify-center transform transition-all duration-300 translate-y-20 opacity-0 z-50">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 15l7-7 7 7"></path></svg>
    </button>

    <script>
        // Load data from python backend
        const articles = {articles_json};
        
        // Load bookmarks from local storage
        let savedIds = JSON.parse(localStorage.getItem('mySavedNewsIds')) || [];
        
        let currentTab = 'all';
        let searchQuery = '';
        
        // DOM Elements
        const feedContainer = document.getElementById('feedContainer');
        const statsBanner = document.getElementById('statsBanner');
        const searchInput = document.getElementById('searchInput');
        const scrollArea = document.getElementById('scrollArea');
        const scrollTopBtn = document.getElementById('scrollTopBtn');
        
        // --- Interactions --- //
        
        // 1. Search Bar Event
        searchInput.addEventListener('input', (e) => {{
            searchQuery = e.target.value.toLowerCase();
            renderFeed(); // Instantly update without server roundtrip!
        }});
        
        // 2. Scroll to top visibility check
        scrollArea.addEventListener('scroll', () => {{
            if (scrollArea.scrollTop > 400) {{
                scrollTopBtn.classList.remove('translate-y-20', 'opacity-0');
            }} else {{
                scrollTopBtn.classList.add('translate-y-20', 'opacity-0');
            }}
        }});
        
        // 3. Tab switching
        function changeTab(tab) {{
            currentTab = tab;
            
            // Switch UI states for tabs
            document.querySelectorAll('.tab-btn').forEach(btn => {{
                if (btn.dataset.tab === tab) {{
                    btn.classList.add('bg-blue-500/20', 'text-blue-400', 'border-blue-500/30');
                    btn.classList.remove('bg-white/5', 'text-gray-400', 'border-transparent');
                }} else {{
                    btn.classList.remove('bg-blue-500/20', 'text-blue-400', 'border-blue-500/30');
                    btn.classList.add('bg-white/5', 'text-gray-400', 'border-transparent');
                }}
            }});
            
            // Bring user back to top perfectly smoothly
            scrollArea.scrollTo(0, 0);
            renderFeed();
        }}
        
        // 4. Bookmark feature
        function toggleBookmark(id, event) {{
            // prevent navigating to link when tapping save button
            event.preventDefault();
            event.stopPropagation();
            
            const index = savedIds.indexOf(id);
            if (index > -1) {{
                savedIds.splice(index, 1); // Remove
            }} else {{
                savedIds.push(id); // Add
            }}
            
            // save back to browser storage
            localStorage.setItem('mySavedNewsIds', JSON.stringify(savedIds));
            
            // Re-render instantly based on context
            if (currentTab === 'saved') {{
                renderFeed();
            }} else {{
                // Optimistic UI update for the single button clicked to prevent flashing
                const btn = document.querySelector(`button[data-id="${{id}}"]`);
                if (btn) {{
                    const isSaved = savedIds.includes(id);
                    btn.innerHTML = isSaved 
                        ? `<svg class="w-5 h-5 text-yellow-500 drop-shadow-md" fill="currentColor" viewBox="0 0 20 20"><path d="M5 4a2 2 0 012-2h6a2 2 0 012 2v14l-5-2.5L5 18V4z"></path></svg>`
                        : `<svg class="w-5 h-5 text-gray-500 hover:text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"></path></svg>`;
                }}
            }}
        }}
        
        // 5. Scroll to top action
        function scrollToTop() {{
            scrollArea.scrollTo({{ top: 0, behavior: 'smooth' }});
        }}
        
        // Utility logic
        function getAccentColor(source) {{
            const src = source.toLowerCase();
            if (src.includes('qiita')) return '#55c500';
            if (src.includes('zenn')) return '#3ea8ff';
            if (src.includes('google')) return '#ea4335';
            if (src.includes('hatena')) return '#008fde';
            if (src.includes('hacker news')) return '#ff6600';
            if (src.includes('techcrunch')) return '#00a562';
            return 'rgba(255,255,255,0.2)'; // default subtle border
        }}

        function isGadget(source) {{
            const gadgets = ['gizmodo', 'engadget', 'wired', 'gigazine', 'itmedia', 'ascii', 'pc watch'];
            const srcLower = source.toLowerCase();
            return gadgets.some(g => srcLower.includes(g));
        }}
        
        // The Engine Renderer
        function renderFeed() {{
            // Apply all filters completely clientside for instant UX
            let filtered = articles.filter(a => {{
                // Search check (using the simplified data structure)
                const matchString = `${{a.title_ja}} ${{a.source}} ${{a.core_sentence}} ${{a.tags.join(' ')}}`.toLowerCase();
                if (searchQuery && !matchString.includes(searchQuery)) return false;
                
                // Tab Context check
                if (currentTab === 'saved') return savedIds.includes(a.id);
                if (currentTab !== 'all') return a.category === currentTab;
                
                return true; // 'all'
            }});
            
            // Empty State Handling
            if (filtered.length === 0) {{
                feedContainer.innerHTML = `
                    <div class="flex flex-col items-center justify-center py-24 text-gray-500">
                        <svg class="w-16 h-16 mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                        <p class="text-[0.9rem]">見つかりませんでした</p>
                    </div>
                `;
                statsBanner.textContent = ``;
                return;
            }}
            
            statsBanner.innerHTML = currentTab === 'saved' 
                ? `保存済みの記事: <span class="text-white">${{filtered.length}}件</span>`
                : `<span class="text-white">${{filtered.length}}件</span> の厳選トップニュース`;
            
            // Build the DOM string efficiently
            const html = filtered.map(a => {{
                const isSaved = savedIds.includes(a.id);
                const accentColor = getAccentColor(a.category);
                
                // Beautiful Pill Tags
                const tagsHtml = (a.tags || []).map(t => 
                    `<span class="inline-flex items-center px-2 py-0.5 rounded text-[0.65rem] font-medium bg-[#58a6ff]/10 text-blue-400 border border-blue-500/20 mr-1.5 mb-2">${{t}}</span>`
                ).join('');
                
                // Core 1-Sentence Summary format
                const summaryHtml = `<p class="text-[0.95rem] font-medium text-gray-300 leading-relaxed mt-3 mb-1 pl-3 border-l-2 border-[#58a6ff]/70">${{a.core_sentence || ''}}</p>`;
                
                return `
                    <div class="relative bg-[#161b22] border border-gray-700/60 rounded-2xl overflow-hidden card-anim shadow-sm">
                        <div class="absolute top-0 left-0 right-0 h-1" style="background-color: ${{accentColor}}"></div>
                        
                        <div class="p-4 pb-0">
                            <!-- Source and Bookmark -->
                            <div class="flex justify-between items-center mb-2.5">
                                <div class="flex items-center gap-2">
                                    <span class="text-[0.65rem] font-bold text-gray-400 bg-white/5 border border-white/5 py-0.5 px-2 rounded uppercase tracking-wider">${{a.source}}</span>
                                </div>
                                <button data-id="${{a.id}}" onclick="toggleBookmark('${{a.id}}', event)" class="p-2 -mr-2 -mt-2 rounded-full hover:bg-white/10 transition z-10 active:scale-90">
                                    ${{isSaved 
                                        ? `<svg class="w-[1.15rem] h-[1.15rem] text-yellow-500 drop-shadow-sm" fill="currentColor" viewBox="0 0 20 20"><path d="M5 4a2 2 0 012-2h6a2 2 0 012 2v14l-5-2.5L5 18V4z"></path></svg>` 
                                        : `<svg class="w-[1.15rem] h-[1.15rem] text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"></path></svg>`
                                    }}
                                </button>
                            </div>
                            
                            <a href="${{a.url}}" target="_blank" class="block outline-none tap-highlight-transparent group hover:opacity-90 transition mt-3">
                                <!-- Title and Tags -->
                                <h2 class="text-[1.15rem] font-bold text-[#e6edf3] mb-2.5 leading-snug tracking-tight group-hover:text-blue-400 transition-colors">${{a.title_ja}}</h2>
                                <div class="flex flex-wrap mb-2">
                                    ${{tagsHtml}}
                                </div>
                                
                                <!-- Core 1-sentence summary -->
                                ${{summaryHtml}}
                            </a>
                        </div>
                        
                        <!-- Actions -->
                        <div class="px-4 py-3 bg-[#11151c] flex justify-between items-center border-t border-gray-800/80 mt-4">
                            <span class="text-[0.7rem] text-gray-500 font-medium flex items-center gap-1.5">
                                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                                読むのに約${{a.read_time_min || 1}}分
                            </span>
                            <a href="${{a.url}}" target="_blank" class="text-blue-400 text-[0.75rem] font-bold tracking-wide flex items-center gap-1.5 bg-[#58a6ff]/10 border border-[#58a6ff]/20 px-3.5 py-1.5 rounded-full hover:bg-[#58a6ff]/20 active:scale-95 transition">
                                記事を読む
                                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M14 5l7 7m0 0l-7 7m7-7H3"></path></svg>
                            </a>
                        </div>
                    </div>
                `;
            }}).join('');
            
            feedContainer.innerHTML = html;
        }}
        
        // Initial Mount
        renderFeed();
    </script>
</body>
</html>
"""

# Render the massive custom component block
# Streamlit acts merely as a data pipeline, bypassing standard UI completely
components.html(html_template, height=800)
