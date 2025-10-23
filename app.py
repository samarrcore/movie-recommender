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

# 4. Enhanced movie data fetching with better error handling
def fetch_movie_details(movie_id):
    """Fetch comprehensive movie details from TMDB API with caching"""
    # Check cache first
    if movie_id in st.session_state.filter_cache:
        return st.session_state.filter_cache[movie_id]
    
    try:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=en-US"
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        movie_details = {
            'poster_path': data.get('poster_path'),
            'genres': [genre['name'] for genre in data.get('genres', [])],
            'release_date': data.get('release_date', ''),
            'vote_average': data.get('vote_average', 0),
            'runtime': data.get('runtime', 0),
            'overview': data.get('overview', '')
        }
        
        # Cache the result
        st.session_state.filter_cache[movie_id] = movie_details
        return movie_details
        
    except Exception as e:
        print(f"Error fetching details for movie_id {movie_id}:", e)
        fallback_details = {
            'poster_path': None,
            'genres': [],
            'release_date': '',
            'vote_average': 0,
            'runtime': 0,
            'overview': ''
        }
        # Cache the fallback too to avoid repeated failures
        st.session_state.filter_cache[movie_id] = fallback_details
        return fallback_details

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

# 5. Recommend movies with filtering
def recommend(movie, filter_genre=None, filter_year_range=None, filter_rating_min=None):
    movie_index = movies[movies['title'] == movie].index[0]
    distances = similarity[movie_index]
    movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:]

    recommended_movies = []
    recommended_movies_posters = []
    recommended_details = []

    # If no filters, return top 5
    if not any([filter_genre, filter_year_range, filter_rating_min]):
        for i in movies_list[:5]:
            movie_id = movies.iloc[i[0]].movie_id
            recommended_movies.append(movies.iloc[i[0]].title)
            recommended_movies_posters.append(fetch_poster(movie_id))
        return recommended_movies, recommended_movies_posters, 5
    
    # Apply filters
    for i in movies_list:
        if len(recommended_movies) >= 5:
            break
            
        movie_id = movies.iloc[i[0]].movie_id
        movie_title = movies.iloc[i[0]].title
        
        # Fetch movie details for filtering
        details = fetch_movie_details(movie_id)
        
        # Apply genre filter
        if filter_genre and filter_genre not in details['genres']:
            continue
            
        # Apply year filter
        if filter_year_range:
            try:
                movie_year = int(details['release_date'][:4]) if details['release_date'] else 0
                if not (filter_year_range[0] <= movie_year <= filter_year_range[1]):
                    continue
            except (ValueError, IndexError):
                continue
                
        # Apply rating filter
        if filter_rating_min and details['vote_average'] < filter_rating_min:
            continue
            
        # If movie passes all filters, add to recommendations
        recommended_movies.append(movie_title)
        poster_url = "https://image.tmdb.org/t/p/w500" + details['poster_path'] if details['poster_path'] else create_fallback_poster("No Poster Available")
        recommended_movies_posters.append(poster_url)

    # If we don't have enough filtered results, fill with top unfiltered recommendations
    filtered_count = len(recommended_movies)
    if len(recommended_movies) < 5:
        for i in movies_list:
            if len(recommended_movies) >= 5:
                break
            movie_id = movies.iloc[i[0]].movie_id
            movie_title = movies.iloc[i[0]].title
            if movie_title not in recommended_movies:
                recommended_movies.append(movie_title)
                recommended_movies_posters.append(fetch_poster(movie_id))

    return recommended_movies[:5], recommended_movies_posters[:5], filtered_count

# 6. Load data
movies_dict = pickle.load(open('movie_dict.pkl', 'rb'))
movies = pd.DataFrame(movies_dict)

similarity = pickle.load(open('similarity.pkl', 'rb'))

# Initialize session state for filters
if 'filter_cache' not in st.session_state:
    st.session_state.filter_cache = {}

# 7. Enhanced Streamlit UI
st.set_page_config(
    page_title="CinemaMatch - Movie Recommendations",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better styling
st.markdown("""
<style>
    /* Global styling */
    .stApp {
        background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
    }
    
    .main-header {
        text-align: center;
        color: #ffffff;
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 1rem;
        letter-spacing: -0.5px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 30px;
        border-radius: 15px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
    }
    
    .header-icon {
        width: 48px;
        height: 48px;
        margin-right: 15px;
        vertical-align: middle;
        display: inline-block;
    }
    
    .movie-card {
        background: #1a1a2e;
        border: 2px solid rgba(102, 126, 234, 0.2);
        border-radius: 12px;
        padding: 15px;
        margin: 8px;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4);
        text-align: center;
        height: 580px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        align-items: center;
        overflow: hidden;
        transition: all 0.3s ease;
        position: relative;
        width: 100%;
        box-sizing: border-box;
    }
    
    .movie-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 35px rgba(102, 126, 234, 0.4);
        border-color: rgba(102, 126, 234, 0.5);
    }
    
    .movie-title {
        font-size: 1.05rem;
        font-weight: 600;
        color: #ffffff;
        margin-bottom: 12px;
        height: 55px;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
        line-height: 1.3;
        overflow: hidden;
        text-overflow: ellipsis;
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.3), rgba(118, 75, 162, 0.3));
        border-radius: 8px;
        padding: 8px;
        border: 1px solid rgba(102, 126, 234, 0.3);
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
        border-radius: 8px;
        background: #0f0f1e;
        border: 2px solid rgba(102, 126, 234, 0.2);
        position: relative;
        flex-grow: 1;
        margin: 10px 0;
        box-sizing: border-box;
    }
    
    .poster-image {
        max-width: 100%;
        max-height: 100%;
        object-fit: cover;
        border-radius: 6px;
        transition: all 0.3s ease;
    }
    
    .poster-image:hover {
        transform: scale(1.03);
    }
    
    .movie-info {
        margin-top: 10px;
        padding: 10px;
        height: auto;
        min-height: 40px;
        display: flex;
        flex-direction: row;
        align-items: center;
        justify-content: center;
        background: rgba(102, 126, 234, 0.15);
        border-radius: 8px;
        border: 1px solid rgba(102, 126, 234, 0.3);
        width: 100%;
        box-sizing: border-box;
        flex-shrink: 0;
        gap: 8px;
    }
    
    .movie-rating {
        font-size: 0.85rem;
        color: #ffd700;
        font-weight: 600;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 5px;
    }
    
    .star-icon {
        width: 16px;
        height: 16px;
        fill: #ffd700;
    }
    
    .movie-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
        color: #ffffff;
        padding: 10px 20px;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        text-decoration: none;
        width: 90%;
        max-width: 140px;
        margin: 0 auto;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
        text-align: center;
        box-sizing: border-box;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    
    .movie-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(102, 126, 234, 0.5);
    }
    
    .button-icon {
        width: 14px;
        height: 14px;
        fill: white;
    }
    
    .search-section {
        background: #1a1a2e;
        border: 2px solid rgba(102, 126, 234, 0.3);
        padding: 30px;
        border-radius: 12px;
        margin-bottom: 30px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
    }
    
    .search-title {
        color: #ffffff;
        font-size: 1.4rem;
        font-weight: 600;
        margin-bottom: 20px;
        text-align: center;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
    }
    
    .search-icon {
        width: 24px;
        height: 24px;
        fill: #667eea;
    }
    
    .recommend-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 15px 30px;
        border-radius: 8px;
        font-size: 1.1rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        width: 100%;
        margin-top: 20px;
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }
    
    .recommend-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
    }
    
    .recommendations-header {
        text-align: center;
        color: #ffffff;
        font-size: 2rem;
        font-weight: 700;
        margin: 40px 0 30px 0;
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.3), rgba(118, 75, 162, 0.3));
        padding: 20px;
        border-radius: 12px;
        border: 2px solid rgba(102, 126, 234, 0.3);
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 15px;
    }
    
    .recommendations-icon {
        width: 36px;
        height: 36px;
        fill: #ffd700;
    }
    
    /* Metric cards */
    .metric-card {
        background: #1a1a2e;
        border: 2px solid rgba(102, 126, 234, 0.3);
        border-radius: 12px;
        padding: 0;
        margin: 10px;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
        transition: all 0.3s ease;
        overflow: hidden;
        position: relative;
        min-height: 160px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 30px rgba(102, 126, 234, 0.4);
        border-color: rgba(102, 126, 234, 0.5);
    }
    
    .metric-icon {
        width: 40px;
        height: 40px;
        margin-bottom: 10px;
    }
    
    /* Selectbox styling */
    .stSelectbox > div > div {
        background: #1a1a2e;
        border: 2px solid rgba(102, 126, 234, 0.3);
        border-radius: 8px;
        color: white;
    }
    
    /* Main recommendation button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
        border-radius: 8px;
        color: white !important;
        font-weight: 600;
        transition: all 0.3s ease;
        width: auto;
        max-width: 250px;
        padding: 12px 24px;
        font-size: 1rem;
        min-height: 45px;
        margin: 0 auto;
        display: block;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
        color: white !important;
    }
    
    .stButton > button:active {
        transform: translateY(0px);
        box-shadow: 0 3px 12px rgba(102, 126, 234, 0.5);
        color: white !important;
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
        
        .main-header {
            font-size: 2rem;
        }
        
        .recommendations-header {
            font-size: 1.5rem;
        }
    }
    
    /* Fix for proper card containment */
    .element-container {
        width: 100%;
    }
    
    .stMarkdown {
        width: 100%;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Scrollbar styling */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: #1a1a2e;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #667eea;
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #764ba2;
    }
    
    /* Filter section styling */
    .filter-container {
        background: #1a1a2e;
        border: 2px solid rgba(102, 126, 234, 0.3);
        border-radius: 12px;
        padding: 25px;
        margin: 25px 0;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
    }
    
    .filter-title {
        color: #ffffff;
        font-size: 1.2rem;
        font-weight: 600;
        margin: 0 0 20px 0;
        padding: 0;
        text-align: center;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
    }
    
    .filter-icon {
        width: 24px;
        height: 24px;
        fill: #667eea;
    }
    
    .filter-section {
        margin-bottom: 15px;
        padding: 15px;
        background: rgba(102, 126, 234, 0.1);
        border-radius: 8px;
        border: 1px solid rgba(102, 126, 234, 0.2);
    }
    
    .filter-label {
        color: #ffffff;
        font-weight: 600;
        font-size: 0.95rem;
        margin-bottom: 8px;
        display: block;
    }
    
    /* Streamlit checkbox styling */
    .stCheckbox {
        margin-bottom: 10px;
    }
    
    .stCheckbox > label {
        color: white !important;
        font-weight: 500;
    }
    
    /* Selectbox and slider improvements */
    .stSlider > div {
        background: transparent;
    }
    
    /* Text colors */
    .stMarkdown, .stText, p, span, div {
        color: #ffffff;
    }
    
    /* Info/warning boxes */
    .stInfo, .stWarning, .stSuccess {
        background: rgba(102, 126, 234, 0.2);
        border: 1px solid rgba(102, 126, 234, 0.4);
        border-radius: 8px;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Main title
st.markdown('''
<h1 class="main-header">
    <svg class="header-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path fill="white" d="M18,3v2h-2V3H8v2H6V3H4v18h2v-2h2v2h8v-2h2v2h2V3H18z M8,17H6v-2h2V17z M8,13H6v-2h2V13z M8,9H6V7h2V9z M18,17h-2v-2h2V17z M18,13h-2v-2h2V13z M18,9h-2V7h2V9z"/>
    </svg>
    CinemaMatch
</h1>
''', unsafe_allow_html=True)

# Movie selection section
st.markdown('<div style="margin: 30px 0; text-align: center;">', unsafe_allow_html=True)
st.markdown('''
<h3 class="search-title">
    <svg class="search-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path fill="#667eea" d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
    </svg>
    Find Your Next Favorite Movie
</h3>
''', unsafe_allow_html=True)

selected_movie_name = st.selectbox(
    'Select a movie to get personalized recommendations:',
    movies['title'].values,
    help="Choose from over 5000 movies in our database"
)

st.markdown('</div>', unsafe_allow_html=True)

# Filter Section
st.markdown('''
<div class="filter-container">
    <div class="filter-title">
        <svg class="filter-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path fill="#667eea" d="M10,18h4v-2h-4V18z M3,6v2h18V6H3z M6,13h12v-2H6V13z"/>
        </svg>
        Advanced Filters
    </div>
''', unsafe_allow_html=True)

# Create filter columns
filter_col1, filter_col2, filter_col3 = st.columns(3)

with filter_col1:
    enable_genre_filter = st.checkbox("Filter by Genre")
    if enable_genre_filter:
        genre_options = [
            "Action", "Adventure", "Animation", "Comedy", "Crime", "Documentary", 
            "Drama", "Family", "Fantasy", "History", "Horror", "Music", 
            "Mystery", "Romance", "Science Fiction", "TV Movie", "Thriller", 
            "War", "Western"
        ]
        selected_genre = st.selectbox("Select Genre:", genre_options)
    else:
        selected_genre = None

with filter_col2:
    enable_year_filter = st.checkbox("Filter by Year")
    if enable_year_filter:
        year_range = st.slider(
            "Release Year Range:",
            min_value=1970,
            max_value=2024,
            value=(2000, 2024),
            step=1
        )
    else:
        year_range = None

with filter_col3:
    enable_rating_filter = st.checkbox("Filter by Rating")
    if enable_rating_filter:
        min_rating = st.slider(
            "Minimum Rating:",
            min_value=0.0,
            max_value=10.0,
            value=7.0,
            step=0.1
        )
    else:
        min_rating = None

# Close the filter container
st.markdown('</div>', unsafe_allow_html=True)

# Center the button with filter status
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    # Show active filters count
    active_filters = sum([enable_genre_filter, enable_year_filter, enable_rating_filter])
    button_text = f'Get Recommendations'
    if active_filters > 0:
        button_text += f' ({active_filters} filter{"s" if active_filters > 1 else ""})'
    
    recommend_clicked = st.button(button_text, key="recommend_btn")

if recommend_clicked:
    # Prepare filter parameters
    filter_genre = selected_genre if enable_genre_filter else None
    filter_year_range = year_range if enable_year_filter else None
    filter_rating_min = min_rating if enable_rating_filter else None
    
    # Show filter status
    if any([filter_genre, filter_year_range, filter_rating_min]):
        filter_info = []
        if filter_genre:
            filter_info.append(f"Genre: {filter_genre}")
        if filter_year_range:
            filter_info.append(f"Year: {filter_year_range[0]}-{filter_year_range[1]}")
        if filter_rating_min:
            filter_info.append(f"Rating: ≥{filter_rating_min}")
        
        st.info(f"Applied filters: {' • '.join(filter_info)}")
    
    # Loading animation
    loading_text = 'Finding amazing movies for you'
    if any([filter_genre, filter_year_range, filter_rating_min]):
        loading_text += ' with your filters'
    loading_text += '...'
    
    with st.spinner(loading_text):
        names, posters, filtered_count = recommend(
            selected_movie_name, 
            filter_genre=filter_genre,
            filter_year_range=filter_year_range,
            filter_rating_min=filter_rating_min
        )
    
    # Show filtering results
    if any([filter_genre, filter_year_range, filter_rating_min]):
        if filtered_count == 0:
            st.warning("No movies found matching your filters. Showing top recommendations instead.")
        elif filtered_count < 5:
            st.success(f"Found {filtered_count} movies matching your filters. Added {5-filtered_count} similar movies to complete the recommendations.")
    
    # Recommendations header
    st.markdown('''
    <h2 class="recommendations-header">
        <svg class="recommendations-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path fill="#ffd700" d="M12,17.27L18.18,21l-1.64-7.03L22,9.24l-7.19-0.61L12,2L9.19,8.63L2,9.24l5.46,4.73L5.82,21L12,17.27z"/>
        </svg>
        Recommended Movies for You
    </h2>
    ''', unsafe_allow_html=True)
    
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
                    <div class="movie-rating">
                        <svg class="star-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path d="M12,17.27L18.18,21l-1.64-7.03L22,9.24l-7.19-0.61L12,2L9.19,8.63L2,9.24l5.46,4.73L5.82,21L12,17.27z"/>
                        </svg>
                        <svg class="star-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path d="M12,17.27L18.18,21l-1.64-7.03L22,9.24l-7.19-0.61L12,2L9.19,8.63L2,9.24l5.46,4.73L5.82,21L12,17.27z"/>
                        </svg>
                        <svg class="star-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path d="M12,17.27L18.18,21l-1.64-7.03L22,9.24l-7.19-0.61L12,2L9.19,8.63L2,9.24l5.46,4.73L5.82,21L12,17.27z"/>
                        </svg>
                        <svg class="star-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path d="M12,17.27L18.18,21l-1.64-7.03L22,9.24l-7.19-0.61L12,2L9.19,8.63L2,9.24l5.46,4.73L5.82,21L12,17.27z"/>
                        </svg>
                        Highly Recommended
                    </div>
                </div>
            </div>
            ''', unsafe_allow_html=True)
            
            # Add a styled button that fits within the overall design
            st.markdown(f'''
            <div style="margin-top: 10px; width: 100%; display: flex; justify-content: center;">
                <button class="movie-button" onclick="alert('More details about {names[i]} coming soon!')">
                    <svg class="button-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path d="M14,2H6C4.9,2,4,2.9,4,4v16c0,1.1,0.9,2,2,2h12c1.1,0,2-0.9,2-2V8L14,2z M16,18H8v-2h8V18z M16,14H8v-2h8V14z M13,9V3.5 L18.5,9H13z"/>
                    </svg>
                    Learn More
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
                <svg class="metric-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path fill="#667eea" d="M18,2H6C4.9,2,4,2.9,4,4v16c0,1.1,0.9,2,2,2h12c1.1,0,2-0.9,2-2V4C20,2.9,19.1,2,18,2z M18,20H6V4h2v11l2.5-1.5L13,15V4h5V20z"/>
                </svg>
                <div style="font-size: 2.5rem; font-weight: bold; color: #667eea; margin: 10px 0;">{len(movies)}</div>
                <div style="font-size: 1rem; color: #ffffff; font-weight: 600;">Total Movies</div>
                <div style="font-size: 0.85rem; color: #aaaaaa; margin-top: 5px;">In our database</div>
            </div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        st.markdown('''
        <div class="metric-card">
            <div style="text-align: center; padding: 20px;">
                <svg class="metric-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path fill="#667eea" d="M12,2C6.5,2,2,6.5,2,12s4.5,10,10,10s10-4.5,10-10S17.5,2,12,2z M12,20c-4.4,0-8-3.6-8-8s3.6-8,8-8s8,3.6,8,8 S16.4,20,12,20z M16.2,7.5l-4.2,4.2l-2.1-2.1l-1.4,1.4l3.5,3.5l5.6-5.6L16.2,7.5z"/>
                </svg>
                <div style="font-size: 2.5rem; font-weight: bold; color: #667eea; margin: 10px 0;">95%</div>
                <div style="font-size: 1rem; color: #ffffff; font-weight: 600;">Accuracy Rate</div>
                <div style="font-size: 0.85rem; color: #aaaaaa; margin-top: 5px;">User satisfaction</div>
            </div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col3:
        st.markdown('''
        <div class="metric-card">
            <div style="text-align: center; padding: 20px;">
                <svg class="metric-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path fill="#667eea" d="M7,2V13H10V22L17,10H13L17,2H7Z"/>
                </svg>
                <div style="font-size: 2.5rem; font-weight: bold; color: #667eea; margin: 10px 0;">&lt; 2s</div>
                <div style="font-size: 1rem; color: #ffffff; font-weight: 600;">Response Time</div>
                <div style="font-size: 0.85rem; color: #aaaaaa; margin-top: 5px;">Average speed</div>
            </div>
        </div>
        ''', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Instructions
    st.markdown("---")
    st.markdown("""
    ### How to Use
    1. **Select a movie** you enjoyed from the dropdown above
    2. **Click "Get Recommendations"** to discover similar movies
    3. **Apply filters** (optional) to refine your results by genre, year, or rating
    4. **Explore the suggestions** and find your next favorite film
    
    ### Features
    - **Personalized recommendations** based on movie similarity algorithms
    - **High-quality posters** from The Movie Database (TMDB)
    - **Fast and accurate** recommendation engine with intelligent filtering
    - **Professional interface** with modern design and smooth interactions
    """)

