import os
import requests
import streamlit as st


# =============================
# CONFIG
# =============================
API_BASE = os.getenv(
    "API_BASE",
    "https://movie-recommender-system-1-9njm.onrender.com"
)
TMDB_IMG = "https://image.tmdb.org/t/p/w500"

st.set_page_config(page_title="Movie Recommender", page_icon="🎬", layout="wide")

# =============================
# STYLES
# =============================
st.markdown(
    """
<style>
.block-container { padding-top: 1rem; padding-bottom: 2rem; max-width: 1400px; }
.small-muted { color:#6b7280; font-size: 0.92rem; }
.movie-title { font-size: 0.9rem; line-height: 1.15rem; height: 2.3rem; overflow: hidden; }
.card { border: 1px solid rgba(0,0,0,0.08); border-radius: 16px; padding: 14px; background: rgba(255,255,255,0.7); }
</style>
""",
    unsafe_allow_html=True,
)

# =============================
# STATE
# =============================
if "view" not in st.session_state:
    st.session_state.view = "home"
if "selected_tmdb_id" not in st.session_state:
    st.session_state.selected_tmdb_id = None

# =============================
# ROUTING
# =============================
def goto_home():
    st.session_state.view = "home"
    st.session_state.selected_tmdb_id = None
    st.rerun()

def goto_details(tmdb_id: int):
    st.session_state.view = "details"
    st.session_state.selected_tmdb_id = int(tmdb_id)
    st.rerun()

# =============================
# API HELPER
# =============================
@st.cache_data(ttl=30)
def api_get_json(path: str, params: dict | None = None):
    try:
        r = requests.get(f"{API_BASE}{path}", params=params, timeout=25)
        if r.status_code >= 400:
            return None, f"HTTP {r.status_code}: {r.text[:300]}"
        return r.json(), None
    except Exception as e:
        return None, f"Request failed: {e}"

# =============================
# POSTER GRID
# =============================
def poster_grid(cards, cols=6, key_prefix="grid"):
    if not cards:
        st.info("No movies to show.")
        return

    rows = (len(cards) + cols - 1) // cols
    idx = 0

    for r in range(rows):
        colset = st.columns(cols)

        for c in range(cols):
            if idx >= len(cards):
                break

            m = cards[idx]
            idx += 1

            tmdb_id = m.get("tmdb_id")
            title = m.get("title", "Untitled")
            poster = m.get("poster_url")

            with colset[c]:
                if poster:
                    st.image(poster, use_container_width=True)
                else:
                    st.write("🖼️ No poster")

                if st.button("Open", key=f"{key_prefix}_{r}_{c}_{idx}_{tmdb_id}"):
                    if tmdb_id:
                        goto_details(tmdb_id)

                st.markdown(
                    f"<div class='movie-title'>{title}</div>",
                    unsafe_allow_html=True,
                )

# =============================
# SIDEBAR
# =============================
with st.sidebar:
    st.markdown("## 🎬 Menu")
    if st.button("🏠 Home"):
        goto_home()

    st.markdown("---")
    st.markdown("### 🏠 Home Feed")

    home_category = st.selectbox(
        "Category",
        ["trending", "popular", "top_rated", "now_playing", "upcoming"],
        index=0,
    )

    grid_cols = st.slider("Grid columns", 4, 8, 6)

# =============================
# HEADER
# =============================
st.title("🎬 Movie Recommender")
st.markdown(
    "<div class='small-muted'>Search → Open → View Details → Get Recommendations</div>",
    unsafe_allow_html=True,
)
st.divider()

# ==========================================================
# HOME VIEW
# ==========================================================
if st.session_state.view == "home":

    typed = st.text_input(
        "Search by movie title",
        placeholder="Type: avenger, batman, love..."
    )

    st.divider()

    # SEARCH MODE
    if typed.strip():

        data, err = api_get_json("/tmdb/search", params={"query": typed.strip()})

        if err or not data:
            st.error(f"Search failed: {err}")
            st.stop()

        cards = []
        results = data.get("results", []) if isinstance(data, dict) else data

        for m in results:
            tmdb_id = m.get("id") or m.get("tmdb_id")
            title = m.get("title")
            poster_path = m.get("poster_path")
            poster_url = m.get("poster_url")

            if poster_path and not poster_url:
                poster_url = f"{TMDB_IMG}{poster_path}"

            if tmdb_id and title:
                cards.append({
                    "tmdb_id": tmdb_id,
                    "title": title,
                    "poster_url": poster_url,
                })

        poster_grid(cards[:24], cols=grid_cols, key_prefix="search")
        st.stop()

    # HOME FEED
    st.markdown(f"### 🏠 {home_category.title()}")

    home_cards, err = api_get_json(
        "/home",
        params={"category": home_category, "limit": 24},
    )

    if err or not home_cards:
        st.error("Could not load home feed.")
        st.stop()

    poster_grid(home_cards, cols=grid_cols, key_prefix="home")

# ==========================================================
# DETAILS VIEW
# ==========================================================
elif st.session_state.view == "details":

    tmdb_id = st.session_state.selected_tmdb_id

    if not tmdb_id:
        st.warning("No movie selected.")
        st.stop()

    top_left, top_right = st.columns([3, 1])

    with top_left:
        st.markdown("### 📄 Movie Details")

    with top_right:
        if st.button("← Back to Home"):
            goto_home()

    data, err = api_get_json(f"/movie/id/{tmdb_id}")

    if err or not data:
        st.error("Could not load movie details.")
        st.stop()

    left, right = st.columns([1, 2.5], gap="large")

    with left:
        if data.get("poster_url"):
            st.image(data["poster_url"], use_container_width=True)

    with right:
        st.markdown(f"## {data.get('title')}")
        st.markdown(
            f"<div class='small-muted'>Release: {data.get('release_date')}</div>",
            unsafe_allow_html=True,
        )

        genres = ", ".join([g["name"] for g in data.get("genres", [])])
        st.markdown(
            f"<div class='small-muted'>Genres: {genres}</div>",
            unsafe_allow_html=True,
        )

        st.markdown("---")
        st.write(data.get("overview"))

    if data.get("backdrop_url"):
        st.image(data["backdrop_url"], use_container_width=True)

    st.divider()
    st.markdown("### 🎯 Recommendations")

    recs, err = api_get_json(
        "/recommend/genre",
        params={"tmdb_id": tmdb_id, "limit": 18},
    )

    if not err and recs:
        poster_grid(recs, cols=grid_cols, key_prefix="rec")
    else:
        st.info("No recommendations available.")
