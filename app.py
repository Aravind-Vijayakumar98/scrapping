import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import re
import glob

# Load dataset dynamically and preprocess
@st.cache_data
def load_data():
    files = glob.glob("imdb_movies_*.csv")
    if not files:
        st.error("No CSV files found.")
        return pd.DataFrame()

    # Load all CSVs into a list and concatenate into a single DataFrame
    df_list = [pd.read_csv(file) for file in files]
    df = pd.concat(df_list, ignore_index=True)

    # Data cleaning and preprocessing
    df["Converted vote"] = pd.to_numeric(df["Converted vote"], errors="coerce")
    df["Rating"] = pd.to_numeric(df["Rating"], errors="coerce")

    # Convert "Duration" from string (e.g., "2h 30m") to minutes
    df["Duration"] = df["Duration"].apply(convert_duration).astype(float)

    return df.dropna()

# Helper function to convert duration to minutes
def convert_duration(duration):
    if isinstance(duration, str):
        match = re.match(r'(?:(\d+)h)?\s*(?:(\d+)m)?', duration)
        hours = int(match.group(1)) * 60 if match.group(1) else 0
        minutes = int(match.group(2)) if match.group(2) else 0
        return hours + minutes
    return duration


# Sidebar filters
def sidebar_filters():
    st.sidebar.header("Filter Movies")

    # Duration filter
    duration_filter = st.sidebar.radio("Select Duration:", ["< 2 hrs", "2 - 3 hrs", "> 3 hrs"])
    rating_threshold = st.sidebar.slider("Minimum Rating", min_value=0.0, max_value=10.0, value=7.0)
    vote_threshold = st.sidebar.number_input("Minimum Votes", min_value=0, value=5000)

    return duration_filter, rating_threshold, vote_threshold


# Apply filters to the DataFrame
def apply_filters(df, duration_filter, rating_threshold, vote_threshold):
    # Apply Duration Filter
    if duration_filter == "< 2 hrs":
        df = df[df["Duration"] < 120]
    elif duration_filter == "2 - 3 hrs":
        df = df[(df["Duration"] >= 120) & (df["Duration"] <= 180)]
    else:
        df = df[df["Duration"] > 180]

    # Apply Rating Filter
    df = df[df["Rating"] >= rating_threshold]

    # Apply Vote Filter
    df = df[df["Converted vote"] >= vote_threshold]

    return df


# Plot top movies
def plot_top_movies(df):
    # Top 10 Movies by Rating & Votes
    st.subheader("Top 10 Movies by Rating & Votes")
    col1, col2 = st.columns(2)

    top_rated = df.nlargest(10, "Rating")
    # st.write(f"Top 10 Rated Movies: {top_rated[['Title', 'Rating']]}")  # Print the top 10 rated movies
    fig1 = px.bar(top_rated, x="Title", y="Rating", title="Top 10 Movies by Rating", color="Rating")
    col1.plotly_chart(fig1, use_container_width=True)

    top_voted = df.nlargest(10, "Converted vote")
    # st.write(f"Top 10 Voted Movies: {top_voted[['Title', 'Converted vote']]}")  # Print the top 10 voted movies
    fig2 = px.bar(top_voted, x="Title", y="Converted vote", title="Top 10 Movies by Votes", color="Converted vote")
    col2.plotly_chart(fig2, use_container_width=True)


# Plot rating distribution
def plot_rating_distribution(df):
    st.subheader("Rating Distribution")
    fig3, ax = plt.subplots()
    sns.histplot(df["Rating"], bins=20, kde=True, ax=ax)
    ax.set_xlabel("Rating")
    st.pyplot(fig3)


# Display shortest and longest movies
def plot_shortest_longest_movies(df):
    st.subheader("Shortest & Longest Movies")
    shortest_movies = df.nsmallest(5, "Duration")[["Title", "Duration"]]
    longest_movies = df.nlargest(5, "Duration")[["Title", "Duration"]]
    st.write("**Shortest Movies**")
    st.dataframe(shortest_movies)
    st.write("**Longest Movies**")
    st.dataframe(longest_movies)


# Correlation analysis: Ratings vs. Votes
def plot_ratings_vs_votes(df):
    st.subheader("Correlation: Ratings vs. Converted vote")
    fig4 = px.scatter(df, x="Converted vote", y="Rating", title="Ratings vs. Votes", color="Rating", size="Converted vote")
    st.plotly_chart(fig4, use_container_width=True)


# Main function to display everything
def main():
    st.title("IMDb Movie Analysis (2024)")

    # Load data
    df = load_data()
    if df.empty:
        return

    # Get filter options
    duration_filter, rating_threshold, vote_threshold = sidebar_filters()

    # Apply filters
    df_filtered = apply_filters(df, duration_filter, rating_threshold, vote_threshold)
    # st.write(f"Filtered DataFrame shape: {df_filtered.shape}")  # Print shape after applying all filters

    # Plot visuals
    plot_top_movies(df_filtered)
    plot_rating_distribution(df_filtered)
    plot_shortest_longest_movies(df_filtered)
    plot_ratings_vs_votes(df_filtered)

    st.write("**Tip:** Use the sidebar filters to customize the data!")


# Run the app
if __name__ == "__main__":
    main()
