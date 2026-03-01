import streamlit as st
import json
import hashlib
import os
import time
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

import threading

flag_path = os.path.join("data", "is_updating.flag")

# Clean up ghost flags older than 10 minutes (crash recovery)
if os.path.exists(flag_path) and time.time() - os.path.getmtime(flag_path) > 600:
    try:
        os.remove(flag_path)
    except:
        pass

is_updating_flag = os.path.exists(flag_path)

# Native Streamlit Button for Manual Refresh (bypasses iframe sandbox)
st.markdown("""
<style>
    /* Floating Update Button (Bottom Left) */
    div[data-testid="stButton"] {
        position: fixed;
        bottom: 24px;
        left: 24px;
        z-index: 1000000 !important;
        width: max-content !important;
    }
    div[data-testid="stButton"] button {
        background-color: rgba(30, 41, 59, 0.85) !important;
        backdrop-filter: blur(8px) !important;
        -webkit-backdrop-filter: blur(8px) !important;
        border: 1px solid rgba(88, 166, 255, 0.3) !important;
        border-radius: 9999px !important;
        padding: 8px 20px !important;
        color: #58a6ff !important;
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.5) !important;
        transition: all 0.2s !important;
        width: max-content !important;
        min-width: 0 !important;
    }
    div[data-testid="stButton"] button:hover {
        background-color: rgba(51, 65, 85, 0.95) !important;
        border-color: rgba(88, 166, 255, 0.6) !important;
        color: white !important;
        box-shadow: 0 10px 20px rgba(88, 166, 255, 0.2) !important;
    }
    div[data-testid="stButton"] button:active {
        transform: scale(0.95) !important;
    }
    div[data-testid="stButton"] p {
        font-weight: 600 !important;
        font-size: 0.85rem !important;
    }
</style>
""", unsafe_allow_html=True)

FORCE_REFRESH = st.button("🔄 最新ニュース取得", disabled=is_updating_flag)
if 'articles' not in st.session_state:
    st.session_state.articles = []
    
# ZERO-LOAD: Instantly load from pre-compiled JSON instead of web scraping
# Hybrid Cloud Approach: Generate it if it doesn't exist or is older than 6 hours
json_path = os.path.join("data", "daily_curation.json")

is_expired = False
if os.path.exists(json_path):
    # 6 hours TTL = 21600 seconds
    file_age = time.time() - os.path.getmtime(json_path)
    if file_age > 21600:
        is_expired = True

if (FORCE_REFRESH or is_expired or not os.path.exists(json_path)) and not is_updating_flag:
    open(flag_path, 'w').close()
    is_updating_flag = True
    
    def background_update():
        try:
            from generate_curation import run_curation
            run_curation()
        except Exception as e:
            print(f"Background Update Error: {e}")
        finally:
            if os.path.exists(flag_path):
                try:
                    os.remove(flag_path)
                except:
                    pass

    t = threading.Thread(target=background_update, daemon=True)
    t.start()
    
# Check if we just finished updating to trigger the success toast
if not is_updating_flag and st.session_state.get('was_updating_flag', False):
    just_updated_flag = True
    st.cache_data.clear()
    if 'articles' in st.session_state:
        del st.session_state.articles
else:
    just_updated_flag = False

st.session_state['was_updating_flag'] = is_updating_flag

# Load the JSON normally (0.1s Zero-Load state)
try:
    with open(json_path, 'r', encoding='utf-8') as f:
        st.session_state.articles = json.load(f)
except Exception:
    st.session_state.articles = []

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
            <div class="flex items-center gap-2">
                <h1 class="text-xl font-bold text-white whitespace-nowrap tracking-tight">AINews Hub</h1>
                <!-- Manual Update Button is now a native Streamlit FAB -->
            </div>
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

    <!-- Toast Notification Container (Fixed position at bottom, above content) -->
    <div id="toastContainer" class="fixed bottom-24 left-1/2 transform -translate-x-1/2 z-[9999999] pointer-events-none flex flex-col items-center justify-end w-full max-w-[90%] transition-all duration-700 opacity-0 translate-y-10">
    </div>

    <!-- Main Content Area where infinite scroll happens natively -->
    <main class="flex-1 overflow-y-auto w-full" id="scrollArea">
        <div class="px-4 py-4 pb-24 flex flex-col gap-4" id="feedContainer">
            <!-- JavaScript dynamically injects cards here -->
        </div>
    </main>

    <!-- Floating Action Button for Scroll to Top -->
    <button id="scrollTopBtn" onclick="scrollToTop()" class="fixed bottom-6 right-6 w-12 h-12 bg-[#58a6ff] hover:bg-blue-500 text-white rounded-full shadow-xl shadow-blue-900/30 flex items-center justify-center transform transition-all duration-300 translate-y-24 opacity-0 z-50">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 15l7-7 7 7"></path></svg>
    </button>
    
    <!-- AI Radio Button -->
    <button id="aiRadioBtn" onclick="toggleAudio()" class="fixed bottom-20 right-6 w-12 h-12 bg-purple-600 hover:bg-purple-500 text-white rounded-full shadow-xl shadow-purple-900/30 flex items-center justify-center transform transition-all duration-300 z-50 group border border-purple-400/30">
        <svg class="w-5 h-5 ml-1" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clip-rule="evenodd"></path></svg>
    </button>

    <script>
        // 1. Data Initialization
        const articles = {articles_json};
        
        const isUpdating = {'true' if is_updating_flag else 'false'};
        const justUpdated = {'true' if just_updated_flag else 'false'};
        
        // Load bookmarks and read status from local storage
        let savedIds = JSON.parse(localStorage.getItem('mySavedNewsIds')) || [];
        let readIds = JSON.parse(localStorage.getItem('myReadNewsIds')) || [];
        
        let currentTab = 'all';
        let searchQuery = '';
        let currentVisibleArticles = [];
        let isPlaying = false;
        let wakeLock = null;
        
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
        
        // 4. Swipe Gesture for Tab Navigation
        let touchStartX = 0;
        let touchStartY = 0;
        const tabOrder = ['all', 'AI・テクノロジートレンド', 'ガジェット・ハードウェア', 'ビジネス・経済', 'ライフハック・仕事術', 'サイエンス・未来予測', 'saved'];

        scrollArea.addEventListener('touchstart', e => {{
            touchStartX = e.changedTouches[0].screenX;
            touchStartY = e.changedTouches[0].screenY;
        }}, {{passive: true}});

        scrollArea.addEventListener('touchend', e => {{
            const touchEndX = e.changedTouches[0].screenX;
            const touchEndY = e.changedTouches[0].screenY;
            const xDiff = touchStartX - touchEndX;
            const yDiff = Math.abs(touchStartY - touchEndY);
            
            // Swipe must be primarily horizontal and exceed 60px distance
            if (Math.abs(xDiff) > 60 && Math.abs(xDiff) > yDiff * 1.5) {{
                const currentIndex = tabOrder.indexOf(currentTab);
                if (currentIndex === -1) return;
                
                let nextIndex = currentIndex;
                if (xDiff > 0 && currentIndex < tabOrder.length - 1) {{
                    // Swiped Left -> Move to next tab
                    nextIndex++;
                }} else if (xDiff < 0 && currentIndex > 0) {{
                    // Swiped Right -> Move to previous tab
                    nextIndex--;
                }}
                
                if (nextIndex !== currentIndex) {{
                    changeTab(tabOrder[nextIndex]);
                    // Auto-scroll the top tab container to keep the active tab visible
                    const targetBtn = document.querySelector(`[data-tab="${{tabOrder[nextIndex]}}"]`);
                    if (targetBtn) {{
                        targetBtn.scrollIntoView({{ behavior: 'smooth', block: 'nearest', inline: 'center' }});
                    }}
                }}
            }}
        }}, {{passive: true}});
        
        // 5. Bookmark feature
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
        
        // 6. Read State Tracking
        function markAsRead(id) {{
            if (!readIds.includes(id)) {{
                readIds.push(id);
                localStorage.setItem('myReadNewsIds', JSON.stringify(readIds));
                
                // Optimistic visual update
                const card = document.getElementById(`card-${{id}}`);
                const dot = document.getElementById(`dot-${{id}}`);
                if(card) card.classList.add('opacity-50', 'grayscale-[30%]');
                if(dot) dot.style.display = 'none';
            }}
        }}

        // 7. AI Radio Functionality
        async function toggleAudio() {{
            const btn = document.getElementById('aiRadioBtn');
            if (isPlaying) {{
                window.speechSynthesis.cancel();
                isPlaying = false;
                btn.innerHTML = `<svg class="w-5 h-5 ml-1" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clip-rule="evenodd"></path></svg>`;
                btn.classList.replace('bg-red-500', 'bg-purple-600');
                btn.classList.replace('shadow-red-900/40', 'shadow-purple-900/30');
                
                // Release wake lock manually
                if (wakeLock !== null) {{
                    try {{
                        await wakeLock.release();
                        wakeLock = null;
                    }} catch (err) {{
                        console.warn('Wake Lock release error:', err);
                    }}
                }}
                return;
            }}
            
            if (currentVisibleArticles.length === 0) return;
            
            isPlaying = true;
            btn.innerHTML = `<svg class="w-5 h-5 animate-pulse" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd"></path></svg>`;
            btn.classList.replace('bg-purple-600', 'bg-red-500');
            btn.classList.replace('shadow-purple-900/30', 'shadow-red-900/40');
            
            // Acquire wake lock to prevent screen sleep during audio
            try {{
                if ('wakeLock' in navigator) {{
                    wakeLock = await navigator.wakeLock.request('screen');
                }}
            }} catch (err) {{
                console.warn('Wake Lock request error:', err);
            }}
            
            let fullText = "AIアナウンサーです。現在画面に表示されているニュースをお読みします。";
            currentVisibleArticles.slice(0, 10).forEach(a => {{
                fullText += `次のニュースです。${{a.title_ja}}。${{a.core_sentence}}。`;
            }});
            fullText += "ニュースは以上です。";
            
            const utterance = new window.SpeechSynthesisUtterance(fullText);
            utterance.lang = 'ja-JP';
            utterance.rate = 1.05;
            
            utterance.onend = async () => {{
                isPlaying = false;
                btn.innerHTML = `<svg class="w-5 h-5 ml-1" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clip-rule="evenodd"></path></svg>`;
                btn.classList.replace('bg-red-500', 'bg-purple-600');
                btn.classList.replace('shadow-red-900/40', 'shadow-purple-900/30');
                
                // Release wake lock when finished
                if (wakeLock !== null) {{
                    try {{
                        await wakeLock.release();
                        wakeLock = null;
                    }} catch (err) {{
                        console.warn('Wake Lock release error:', err);
                    }}
                }}
            }};
            
            window.speechSynthesis.speak(utterance);
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
            
            currentVisibleArticles = filtered;
            
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
                const isRead = readIds.includes(a.id);
                const accentColor = getAccentColor(a.category);
                
                const opacityClass = isRead ? 'opacity-50 grayscale-[30%] transition-all' : '';
                const blueDot = isRead ? '' : `<span id="dot-${{a.id}}" class="inline-block w-2.5 h-2.5 bg-blue-500 rounded-full shadow-[0_0_8px_rgba(59,130,246,0.8)] ml-2 mb-0.5 animate-pulse"></span>`;
                
                // Beautiful Pill Tags
                const tagsHtml = (a.tags || []).map(t => 
                    `<span class="inline-flex items-center px-2 py-0.5 rounded text-[0.65rem] font-medium bg-[#58a6ff]/10 text-blue-400 border border-blue-500/20 mr-1.5 mb-2">${{t}}</span>`
                ).join('');
                
                // Core 1-Sentence Summary format
                const summaryHtml = `<p class="text-[0.95rem] font-medium text-gray-300 leading-relaxed mt-3 mb-1 pl-3 border-l-2 border-[#58a6ff]/70">${{a.core_sentence || ''}}</p>`;
                
                // Beautiful Insight Display
                const insightHtml = a.insight 
                    ? `<p class="text-[0.85rem] font-semibold text-amber-200/90 mt-3 pt-2 border-t border-gray-700/50">${{a.insight}}</p>` 
                    : '';
                
                return `
                    <div id="card-${{a.id}}" class="relative bg-[#161b22] border border-gray-700/60 rounded-2xl overflow-hidden card-anim shadow-sm ${{opacityClass}}">
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
                            
                            <a href="${{a.url}}" target="_blank" onclick="markAsRead('${{a.id}}')" class="block outline-none tap-highlight-transparent group hover:opacity-90 transition mt-3">
                                <!-- Title and Tags -->
                                <h2 class="text-[1.15rem] font-bold text-[#e6edf3] mb-2.5 leading-snug tracking-tight group-hover:text-blue-400 transition-colors">${{a.title_ja}}${{blueDot}}</h2>
                                <div class="flex flex-wrap mb-2">
                                    ${{tagsHtml}}
                                </div>
                                
                                <!-- Core 1-sentence summary & Insight -->
                                ${{summaryHtml}}
                                ${{insightHtml}}
                            </a>
                        </div>
                        
                        <!-- Actions -->
                        <div class="px-4 py-3 bg-[#11151c] flex justify-between items-center border-t border-gray-800/80 mt-4">
                            <span class="text-[0.7rem] text-gray-500 font-medium flex items-center gap-1.5">
                                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                                読むのに約${{a.read_time_min || 1}}分
                            </span>
                            <a href="${{a.url}}" target="_blank" onclick="markAsRead('${{a.id}}')" class="text-blue-400 text-[0.75rem] font-bold tracking-wide flex items-center gap-1.5 bg-[#58a6ff]/10 border border-[#58a6ff]/20 px-3.5 py-1.5 rounded-full hover:bg-[#58a6ff]/20 active:scale-95 transition">
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
        
        // --- Toast Notification System --- //
        function showToast(htmlContent, persistent = false) {{
            const container = document.getElementById('toastContainer');
            container.innerHTML = `
                <div class="bg-[#1f242c]/95 backdrop-blur-md text-white border border-gray-700/50 shadow-2xl rounded-full px-5 py-2.5 text-sm font-medium flex items-center shadow-blue-900/10">
                    ${{htmlContent}}
                </div>
            `;
            
            // Animate in
            requestAnimationFrame(() => {{
                container.classList.remove('opacity-0', 'translate-y-10');
                container.classList.add('opacity-100', 'translate-y-0');
            }});
            
            if (!persistent) {{
                setTimeout(() => {{
                    container.classList.remove('opacity-100', 'translate-y-0');
                    container.classList.add('opacity-0', 'translate-y-10');
                }}, 4000);
            }}
        }}

        // Trigger on load based on Python flags
        if (justUpdated) {{
            showToast("✨ 新しいニュースが届きました。最新のフィードです。");
        }} else if (isUpdating) {{
            showToast(`
                <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-blue-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span class="text-[#c9d1d9] tracking-tight">最新ニュースをキュレーション中... <span class="text-gray-500 text-xs ml-1 whitespace-nowrap">(操作可能です)</span></span>
            `, true);
        }}
    </script>
</body>
</html>
"""

# Render the massive custom component block
# Streamlit acts merely as a data pipeline, bypassing standard UI completely
components.html(html_template, height=800)

# --- Seamless Background Update Poller ---
if is_updating_flag:
    # Hang the python script execution while the background thread does its job.
    # Because Streamlit streams HTML down to the browser before reaching here,
    # the frontend renders perfectly and remains fully interactive!
    while os.path.exists(flag_path):
        time.sleep(1)
    
    # Once the file is deleted (thread finished), auto-rerun to naturally push new data.
    st.rerun()
