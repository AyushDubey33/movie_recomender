import requests
import streamlit as st

# =============================
# CONFIG
# =============================
API_BASE = "http://127.0.0.1:8000"   # change to render URL if deployed
TMDB_IMG = "https://image.tmdb.org/t/p/w500"

st.set_page_config(page_title="Movie Recommender", page_icon="🎬", layout="wide")

# =============================
# DARK MODE TOGGLE
# =============================
dark_mode = st.sidebar.toggle("🌙 Dark Mode", value=False)

if dark_mode:
    st.markdown("""
        <style>
        body { background-color: #0e1117; color: white; }
        .card { background-color: #1c1f26; color: white; }
        </style>
    """, unsafe_allow_html=True)

# =============================
# STATE
# =============================
if "view" not in st.session_state:
    st.session_state.view = "home"
if "selected_tmdb_id" not in st.session_state:
    st.session_state.selected_tmdb_id = None

# =============================
# NAVIGATION
# =============================
def goto_home():
    st.session_state.view = "home"

def goto_details(tmdb_id):
    st.session_state.view = "details"
    st.session_state.selected_tmdb_id = tmdb_id

# =============================
# API HELPER
# =============================
@st.cache_data(ttl=60)
def api_get(path, params=None):
    try:
        r = requests.get(f"{API_BASE}{path}", params=params, timeout=20)
        if r.status_code != 200:
            return None
        return r.json()
    except:
        return None

# =============================
# GRID UI
# =============================
def show_movies(movies, cols=6):
    if not movies:
        st.warning("No movies found")
        return

    for i in range(0, len(movies), cols):
        row = st.columns(cols)
        for j, m in enumerate(movies[i:i+cols]):
            with row[j]:
                if m.get("poster_url"):
                    st.image(m["poster_url"], width="stretch")

                if st.button(m["title"], key=f"{m['tmdb_id']}_{i}_{j}"):
                    goto_details(m["tmdb_id"])

# =============================
# SIDEBAR
# =============================
with st.sidebar:
    st.title("🎬 Menu")

    if st.button("🏠 Home"):
        goto_home()

    category = st.selectbox(
        "Category",
        ["trending", "popular", "top_rated", "now_playing", "upcoming"]
    )

    cols = st.slider("Columns", 4, 8, 6)

# =============================
# HEADER
# =============================
st.title("🎬 Movie Recommender")

# =============================
# HOME PAGE
# =============================
if st.session_state.view == "home":

    query = st.text_input("Search movie...")

    # SEARCH
    if query:
        data = api_get("/tmdb/search", {"query": query})

        if data and "results" in data:
            movies = []
            for m in data["results"]:
                movies.append({
                    "tmdb_id": m["id"],
                    "title": m["title"],
                    "poster_url": f"{TMDB_IMG}{m['poster_path']}" if m.get("poster_path") else None
                })

            st.subheader("Search Results")
            show_movies(movies, cols)

        else:
            st.error("Search failed")

    # HOME FEED
    else:
        data = api_get("/home", {"category": category})

        if data:
            st.subheader(f"{category.upper()} Movies")
            show_movies(data, cols)
        else:
            st.error("Backend not running")

# =============================
# DETAILS PAGE
# =============================
elif st.session_state.view == "details":

    tmdb_id = st.session_state.selected_tmdb_id

    if st.button("⬅ Back"):
        goto_home()

    data = api_get(f"/movie/id/{tmdb_id}")

    if not data:
        st.error("Failed to load details")
        st.stop()

    col1, col2 = st.columns([1, 2])

    with col1:
        if data.get("poster_url"):
            st.image(data["poster_url"], width="stretch")

    with col2:
        st.title(data["title"])
        st.write("📅", data.get("release_date"))
        st.write("🎭", ", ".join([g["name"] for g in data.get("genres", [])]))
        st.write(data.get("overview"))

    if data.get("backdrop_url"):
        st.image(data["backdrop_url"], width="stretch")

    # =============================
    # RECOMMENDATIONS
    # =============================
    bundle = api_get("/movie/search", {
        "query": data["title"]
    })

    if bundle:

        # TF-IDF
        st.subheader("🔎 Similar Movies")

        tfidf_movies = []
        for x in bundle.get("tfidf_recommendations", []):
            if x.get("tmdb"):
                tfidf_movies.append({
                    "tmdb_id": x["tmdb"]["tmdb_id"],
                    "title": x["tmdb"]["title"],
                    "poster_url": x["tmdb"]["poster_url"]
                })

        show_movies(tfidf_movies, cols)

        # GENRE
        st.subheader("🎭 More Like This")

        show_movies(bundle.get("genre_recommendations", []), cols)

    else:
        st.warning("No recommendations")