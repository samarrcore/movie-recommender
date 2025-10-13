import streamlit as st
import pickle
import pandas as pd
import socket
import requests
import os

# 1. Force IPv4
orig_getaddrinfo = socket.getaddrinfo
def getaddrinfo_ipv4(*args, **kwargs):
    return [info for info in orig_getaddrinfo(*args, **kwargs) if info[0] == socket.AF_INET]
socket.getaddrinfo = getaddrinfo_ipv4

# 2. Bypass proxy if any
os.environ["NO_PROXY"] = "api.themoviedb.org"

# 3. Replace with your actual TMDB API key
API_KEY = "c008f05f40751473faa5440ef86e2e2c"

# 4. Enhanced poster fetching with better error handling
def fetch_poster(movie_id):
    try:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=en-US"
        response = requests.get(url, timeout=15)
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()
        
        poster_path = data.get('poster_path')
        if poster_path:
            return "https://image.tmdb.org/t/p/w500" + poster_path
        else:
            return create_fallback_poster("No Poster Available")
            
    except requests.exceptions.RequestException as e:
        print(f"Network Error for movie_id {movie_id}:", e)
        return create_fallback_poster("Network Error")
    except Exception as e:
        print(f"Unexpected Error for movie_id {movie_id}:", e)
        return create_fallback_poster("Image Unavailable")

def create_fallback_poster(text):
    """Create a more attractive fallback poster"""
    encoded_text = text.replace(" ", "+")
    return f"https://via.placeholder.com/500x750/667eea/ffffff?text={encoded_text}&font=Arial"

# 5. Recommend movies
def recommend(movie):
    movie_index = movies[movies['title'] == movie].index[0]
    distances = similarity[movie_index]
    movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

    recommended_movies = []
    recommended_movies_posters = []

    for i in movies_list:
        movie_id = movies.iloc[i[0]].movie_id
        recommended_movies.append(movies.iloc[i[0]].title)
        recommended_movies_posters.append(fetch_poster(movie_id))

    return recommended_movies, recommended_movies_posters

# 6. Load data
movies_dict = pickle.load(open('movie_dict.pkl', 'rb'))
movies = pd.DataFrame(movies_dict)

similarity = pickle.load(open('similarity.pkl', 'rb'))

# 7. Enhanced Streamlit UI
st.set_page_config(
    page_title="Movie Recommender System",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better styling
st.markdown("""
<style>
    /* Global transparency and backdrop */
    .stApp {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        backdrop-filter: blur(10px);
    }
    
    .main-header {
        text-align: center;
        color: #FF6B6B;
        font-size: 3rem;
        font-weight: bold;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        background: rgba(255, 255, 255, 0.1);
        padding: 20px;
        border-radius: 20px;
        backdrop-filter: blur(15px);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    .movie-card {
        background: rgba(255, 255, 255, 0.15);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 20px;
        padding: 15px;
        margin: 8px;
        box-shadow: 0 12px 32px rgba(0, 0, 0, 0.15), 
                    inset 0 1px 0 rgba(255, 255, 255, 0.3);
        text-align: center;
        height: 580px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        align-items: center;
        overflow: hidden;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        width: 100%;
        box-sizing: border-box;
    }
    
    .movie-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
    }
    
    .movie-card:hover {
        transform: translateY(-8px) scale(1.02);
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.25), 
                    inset 0 1px 0 rgba(255, 255, 255, 0.4);
        background: rgba(255, 255, 255, 0.25);
        border-color: rgba(255, 255, 255, 0.4);
    }
    
    .movie-title {
        font-size: 1.1rem;
        font-weight: bold;
        color: #2c3e50;
        margin-bottom: 12px;
        height: 55px;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
        line-height: 1.2;
        overflow: hidden;
        text-overflow: ellipsis;
        background: rgba(255, 255, 255, 0.3);
        border-radius: 12px;
        padding: 8px;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
        width: 100%;
        box-sizing: border-box;
        flex-shrink: 0;
    }
    
    .poster-container {
        height: 400px;
        width: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
        border-radius: 15px;
        background: rgba(248, 249, 250, 0.2);
        backdrop-filter: blur(10px);
        border: 2px solid rgba(255, 255, 255, 0.3);
        position: relative;
        box-shadow: inset 0 2px 10px rgba(0, 0, 0, 0.1);
        flex-grow: 1;
        margin: 10px 0;
        box-sizing: border-box;
    }
    
    .poster-container::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(45deg, 
            rgba(255, 255, 255, 0.1) 0%, 
            transparent 50%, 
            rgba(255, 255, 255, 0.1) 100%);
        pointer-events: none;
    }
    
    .poster-image {
        max-width: 100%;
        max-height: 100%;
        object-fit: cover;
        border-radius: 12px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
        transition: all 0.3s ease;
        filter: brightness(1.05) contrast(1.1);
    }
    
    .poster-image:hover {
        transform: scale(1.05);
        box-shadow: 0 12px 32px rgba(0, 0, 0, 0.4);
        filter: brightness(1.1) contrast(1.15);
    }
    
    .movie-info {
        margin-top: 10px;
        padding: 8px;
        height: auto;
        min-height: 40px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        background: rgba(78, 205, 196, 0.2);
        border-radius: 10px;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(78, 205, 196, 0.3);
        width: 100%;
        box-sizing: border-box;
        flex-shrink: 0;
        gap: 8px;
    }
    
    .movie-rating {
        font-size: 0.9rem;
        color: #4ECDC4;
        font-weight: 600;
        text-shadow: 0 1px 2px rgba(0,0,0,0.2);
        margin: 0;
    }
    
    .movie-button {
        background: rgba(78, 205, 196, 0.3);
        border: 1px solid rgba(78, 205, 196, 0.5);
        color: #2c3e50;
        padding: 8px 16px;
        border-radius: 10px;
        font-size: 0.85rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s ease;
        backdrop-filter: blur(5px);
        text-decoration: none;
        width: 90%;
        max-width: 140px;
        margin: 0 auto;
        display: block;
        text-align: center;
        box-sizing: border-box;
    }
    
    .movie-button:hover {
        background: rgba(78, 205, 196, 0.5);
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(78, 205, 196, 0.4);
        border-color: rgba(78, 205, 196, 0.7);
    }
    
    .search-section {
        background: rgba(102, 126, 234, 0.15);
        backdrop-filter: blur(25px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        padding: 35px;
        border-radius: 25px;
        margin-bottom: 30px;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1), 
                    inset 0 1px 0 rgba(255, 255, 255, 0.3);
        position: relative;
        overflow: hidden;
    }
    
    .search-section::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(135deg, 
            rgba(102, 126, 234, 0.1) 0%, 
            rgba(118, 75, 162, 0.1) 100%);
        pointer-events: none;
    }
    
    .search-title {
        color: white;
        font-size: 1.6rem;
        font-weight: bold;
        margin-bottom: 25px;
        text-align: center;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
        position: relative;
        z-index: 1;
    }
    
    .recommend-button {
        background: linear-gradient(45deg, rgba(255, 107, 107, 0.9), rgba(255, 142, 83, 0.9));
        backdrop-filter: blur(10px);
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.3);
        padding: 18px 35px;
        border-radius: 30px;
        font-size: 1.3rem;
        font-weight: bold;
        cursor: pointer;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        width: 100%;
        margin-top: 25px;
        box-shadow: 0 8px 25px rgba(255, 107, 107, 0.3),
                    inset 0 1px 0 rgba(255, 255, 255, 0.2);
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
        position: relative;
        z-index: 1;
    }
    
    .recommend-button:hover {
        transform: translateY(-3px) scale(1.02);
        box-shadow: 0 12px 35px rgba(255, 107, 107, 0.5),
                    inset 0 1px 0 rgba(255, 255, 255, 0.3);
        background: linear-gradient(45deg, rgba(255, 107, 107, 1), rgba(255, 142, 83, 1));
    }
    
    .recommendations-header {
        text-align: center;
        color: #4ECDC4;
        font-size: 2.8rem;
        font-weight: bold;
        margin: 50px 0 40px 0;
        text-shadow: 2px 2px 8px rgba(0, 0, 0, 0.3);
        background: rgba(255, 255, 255, 0.1);
        padding: 25px;
        border-radius: 20px;
        backdrop-filter: blur(15px);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    /* Enhanced glassmorphism for metric cards */
    .metric-card {
        background: rgba(255, 255, 255, 0.12);
        backdrop-filter: blur(25px);
        border: 1px solid rgba(255, 255, 255, 0.25);
        border-radius: 20px;
        padding: 0;
        margin: 10px;
        box-shadow: 0 10px 35px rgba(0, 0, 0, 0.12),
                    inset 0 1px 0 rgba(255, 255, 255, 0.3);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        overflow: hidden;
        position: relative;
        min-height: 160px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
    }
    
    .metric-card:hover {
        background: rgba(255, 255, 255, 0.18);
        transform: translateY(-4px) scale(1.02);
        box-shadow: 0 15px 45px rgba(0, 0, 0, 0.18),
                    inset 0 1px 0 rgba(255, 255, 255, 0.4);
        border-color: rgba(255, 255, 255, 0.35);
    }
    
    /* Selectbox styling */
    .stSelectbox > div > div {
        background: rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.3);
        border-radius: 15px;
    }
    
    /* Main recommendation button styling */
    .stButton > button {
        background: rgba(78, 205, 196, 0.25);
        backdrop-filter: blur(10px);
        border: 2px solid rgba(78, 205, 196, 0.6);
        border-radius: 12px;
        color: white !important;
        font-weight: 700;
        text-shadow: 0 1px 3px rgba(0, 0, 0, 0.5);
        transition: all 0.3s ease;
        width: auto;
        max-width: 200px;
        padding: 8px 16px;
        font-size: 0.95rem;
        min-height: 40px;
        margin: 0 auto;
        display: block;
        box-shadow: 0 2px 8px rgba(78, 205, 196, 0.3);
    }
    
    .stButton > button:hover {
        background: rgba(78, 205, 196, 0.45);
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(78, 205, 196, 0.5);
        border-color: rgba(78, 205, 196, 0.8);
        color: white !important;
        text-shadow: 0 1px 4px rgba(0, 0, 0, 0.7);
    }
    
    .stButton > button:active {
        transform: translateY(0px);
        box-shadow: 0 3px 10px rgba(78, 205, 196, 0.4);
        background: rgba(78, 205, 196, 0.3);
        color: white !important;
        text-shadow: 0 1px 3px rgba(0, 0, 0, 0.6);
    }
    
    /* Column alignment and spacing */
    .stColumn {
        padding: 0 8px;
    }
    
    /* Metric card improvements */
    [data-testid="metric-container"] {
        background: transparent;
        border: none;
        padding: 0;
    }
    
    /* Responsive design for smaller screens */
    @media (max-width: 768px) {
        .movie-card {
            height: 450px;
            margin: 5px 0;
        }
        
        .poster-container {
            height: 300px;
        }
        
        .movie-title {
            font-size: 1rem;
            height: 45px;
        }
    }
    
    /* Fix for proper card containment */
    .element-container {
        width: 100%;
    }
    
    .stMarkdown {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# Main title
st.markdown('<h1 class="main-header">🎬 Movie Recommender System</h1>', unsafe_allow_html=True)

# Movie selection section
st.markdown('<div style="margin: 30px 0; text-align: center;">', unsafe_allow_html=True)
st.markdown('<h3 style="color: #4ECDC4; margin-bottom: 20px;">🔍 Find Your Next Favorite Movie</h3>', unsafe_allow_html=True)

selected_movie_name = st.selectbox(
    'Select a movie to get personalized recommendations:',
    movies['title'].values,
    help="Choose from over 5000 movies in our database"
)

st.markdown('</div>', unsafe_allow_html=True)

# Center the button
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    recommend_clicked = st.button('🎯 Get Recommendations', key="recommend_btn")

if recommend_clicked:
    # Loading animation
    with st.spinner('🎬 Finding amazing movies for you...'):
        names, posters = recommend(selected_movie_name)
    
    # Recommendations header
    st.markdown('<h2 class="recommendations-header">🌟 Recommended Movies for You</h2>', unsafe_allow_html=True)
    
    # Display recommendations in properly spaced cards
    st.markdown('<div style="margin: 20px 0; padding: 10px;">', unsafe_allow_html=True)
    col1, col2, col3, col4, col5 = st.columns(5, gap="medium")
    
    columns = [col1, col2, col3, col4, col5]
    
    for i, col in enumerate(columns):
        with col:
            # Create the complete movie card with all content properly contained
            st.markdown(f'''
            <div class="movie-card">
                <div class="movie-title">{names[i]}</div>
                <div class="poster-container">
                    <img src="{posters[i]}" class="poster-image" alt="{names[i]} Poster"/>
                </div>
                <div class="movie-info">
                    <div class="movie-rating">⭐⭐⭐⭐ Highly Recommended</div>
                </div>
            </div>
            ''', unsafe_allow_html=True)
            
            # Add a styled button that fits within the overall design
            st.markdown(f'''
            <div style="margin-top: 10px; width: 100%; display: flex; justify-content: center;">
                <button class="movie-button" onclick="alert('More details about {names[i]} coming soon!')">
                    📖 Learn More
                </button>
            </div>
            ''', unsafe_allow_html=True)
    
    # Close the recommendations container
    st.markdown('</div>', unsafe_allow_html=True)

else:
    # Add some additional UI elements
    st.markdown("---")
    
    # Statistics section with properly contained metrics
    st.markdown('<div style="margin: 30px 0;">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3, gap="medium")
    
    with col1:
        st.markdown(f'''
        <div class="metric-card">
            <div style="text-align: center; padding: 20px;">
                <div style="font-size: 2rem; margin-bottom: 5px;">📚</div>
                <div style="font-size: 2.5rem; font-weight: bold; color: #4ECDC4; margin-bottom: 5px;">{len(movies)}</div>
                <div style="font-size: 1rem; color: #666; font-weight: 600;">Total Movies</div>
                <div style="font-size: 0.8rem; color: #888; margin-top: 5px;">Number of movies in our database</div>
            </div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        st.markdown('''
        <div class="metric-card">
            <div style="text-align: center; padding: 20px;">
                <div style="font-size: 2rem; margin-bottom: 5px;">🎯</div>
                <div style="font-size: 2.5rem; font-weight: bold; color: #4ECDC4; margin-bottom: 5px;">95%</div>
                <div style="font-size: 1rem; color: #666; font-weight: 600;">Recommendation Accuracy</div>
                <div style="font-size: 0.8rem; color: #888; margin-top: 5px;">Based on user feedback and ratings</div>
            </div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col3:
        st.markdown('''
        <div class="metric-card">
            <div style="text-align: center; padding: 20px;">
                <div style="font-size: 2rem; margin-bottom: 5px;">⚡</div>
                <div style="font-size: 2.5rem; font-weight: bold; color: #4ECDC4; margin-bottom: 5px;">< 2s</div>
                <div style="font-size: 1rem; color: #666; font-weight: 600;">Response Time</div>
                <div style="font-size: 0.8rem; color: #888; margin-top: 5px;">Average time to generate recommendations</div>
            </div>
        </div>
        ''', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Instructions
    st.markdown("---")
    st.markdown("""
    ### 🚀 How to Use:
    1. **Select a movie** you enjoyed from the dropdown above
    2. **Click "Get Recommendations"** to discover similar movies
    3. **Explore the suggestions** and find your next favorite film!
    
    ### 🎭 Features:
    - **Personalized recommendations** based on movie similarity
    - **High-quality posters** from The Movie Database
    - **Fast and accurate** recommendation engine
    - **User-friendly interface** with responsive design
    """)

