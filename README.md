# Movie Recommender System

A content-based movie recommendation system that suggests movies similar to a given title using natural language processing techniques and similarity metrics.

---

## Overview

This project recommends movies based on content similarity such as genres, keywords, cast, and crew. Unlike collaborative filtering, which depends on user interactions, this system focuses on the intrinsic attributes of movies.

The system processes movie metadata, converts it into numerical feature vectors, and computes similarity scores to recommend relevant movies.

---

## Methodology

### 1. Data Collection

The dataset includes the following attributes:

* Title
* Genres
* Keywords
* Cast
* Crew

### 2. Data Preprocessing

* Combine relevant features into a single text representation
* Normalize and clean textual data
* Remove inconsistencies such as spaces and formatting issues

### 3. Feature Extraction

* Apply Bag of Words (BoW) using `CountVectorizer`
* Convert textual data into numerical vectors

### 4. Similarity Computation

* Compute similarity using Cosine Similarity between movie vectors

### 5. Recommendation Generation

* Given a movie title, return the top N most similar movies

---

## Technology Stack

* Programming Language: Python

* Libraries:

  * Pandas
  * NumPy
  * Scikit-learn

* Core Concepts:

  * Natural Language Processing (BoW)
  * Cosine Similarity
  * Content-Based Filtering

---

## Project Structure

```
movie-recommender/
│
├── data/
│   └── movies.csv
│
├── model/
│   ├── similarity.pkl
│   └── movie_list.pkl
│
├── app.py
├── recommender.py
├── requirements.txt
└── README.md
```

---

## Execution Instructions

1. Clone the repository:

```
git clone https://github.com/your-username/movie-recommender.git
cd movie-recommender
```

2. Install dependencies:

```
pip install -r requirements.txt
```

3. Run the application:

```
python app.py
```

Alternatively, if using Streamlit:

```
streamlit run app.py
```

---

## Example

Input:

```
Avatar
```

Output:

```
- Guardians of the Galaxy
- John Carter
- Star Trek
- Avengers
- Interstellar
```

---

## Limitations

* Does not incorporate user-specific preferences
* Duplicate movie titles may lead to incorrect mappings
* Performance depends on the quality of metadata
* External API integrations (e.g., posters) may fail due to network issues

---

## Future Work

* Integrate collaborative filtering for personalization
* Use TF-IDF or embedding-based representations
* Resolve duplicate title ambiguity using unique identifiers
* Integrate external APIs for enhanced metadata
* Deploy as a full-stack web application

---

## Learning Outcomes

* Implementation of NLP techniques for recommendation systems
* Understanding and application of similarity metrics
* Data preprocessing and feature engineering
* Development of an end-to-end machine learning pipeline

---

## Contribution

Contributions are welcome. Fork the repository and submit a pull request for improvements.

---

## License

This project is licensed under the MIT License.

---

## Author
Samar Pratap Singh
