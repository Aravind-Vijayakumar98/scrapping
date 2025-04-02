import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import mysql.connector
from webdriver_manager.microsoft import EdgeChromiumDriverManager

# **MySQL Database Connection**
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Aravi@2106",
    database="imdb"
)
cursor = db.cursor()

# **Genres to Scrape**
selected_genres = ["Action", "Comedy", "Drama", "Horror", "Family"]

# **Setup Edge WebDriver**
options = webdriver.EdgeOptions()
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36")

service = Service(EdgeChromiumDriverManager().install())
driver = webdriver.Edge(service=service, options=options)

# **Open IMDb 2024 Movies Page**
url = "https://www.imdb.com/search/title/?title_type=feature&release_date=2024-01-01,2024-12-31"
driver.get(url)
time.sleep(5)

# **Function to Convert Votes**
def convert_votes(votes):
    if not votes or votes == "N/A":
        return None  
    votes = votes.lower().replace(',', '')
    if 'k' in votes:
        return int(float(votes.replace('k', '')) * 1000)
    elif 'm' in votes:
        return int(float(votes.replace('m', '')) * 1000000)
    return int(votes)

# **Create Tables for Each Genre**
for genre in selected_genres:
    table_name = genre.lower().replace('-', '_')
    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        id INT AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(255),
        rating VARCHAR(10),
        votes VARCHAR(50),
        duration VARCHAR(20),
        converted_vote INT
    )
    """
    cursor.execute(create_table_query)
db.commit()

# **Iterate Over Genres & Scrape Data**
for genre in selected_genres:
    try:
        genre_button = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.XPATH, "//span[@class='ipc-accordion__item__chevron']"))
)
        driver.execute_script("arguments[0].scrollIntoView();", genre_button)
        driver.execute_script("arguments[0].click();", genre_button)
        time.sleep(3)

        # **Load All Movies (Click '50 more' Button)**
        for _ in range(3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            try:
                next_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), '50 more')]/ancestor::button"))
                )
                driver.execute_script("arguments[0].click();", next_button)
                time.sleep(5)
            except:
                print(f"No more '50 more' button for {genre}.")
                break

        movies = driver.find_elements(By.XPATH, "//li[contains(@class, 'ipc-metadata-list-summary-item')]")
        
        genre_movie_data = []

        for movie in movies:
            try:
                title = movie.find_element(By.XPATH, ".//h3[contains(@class, 'ipc-title__text')]").text
                rating_element = movie.find_elements(By.XPATH, ".//span[contains(@class, 'ipc-rating-star--rating')]")
                rating = rating_element[0].text if rating_element else "N/A"
                votes_element = movie.find_elements(By.XPATH, ".//span[contains(@class, 'ipc-rating-star--voteCount')]")
                votes = votes_element[0].text.replace('(', '').replace(')', '') if votes_element else "N/A"
                converted_vote = convert_votes(votes)
                duration_element = movie.find_elements(By.XPATH, ".//span[contains(@class, 'hvVhYi')]")
                
                duration = duration_element[1].text if duration_element else "N/A"

                genre_movie_data.append((title, rating, votes, duration, converted_vote))
            except Exception as e:
                print(f"Skipping movie due to error: {e}")

        table_name = genre.lower().replace('-', '_')
        df = pd.DataFrame(genre_movie_data, columns=["Title", "Rating", "Votes", "Duration", "Converted vote"])
        df.to_csv(f"imdb_movies_{table_name}.csv", index=False, encoding='utf-8')

        if genre_movie_data:
            insert_query = f"INSERT INTO {table_name} (title, rating, votes, duration, converted_vote) VALUES (%s, %s, %s, %s, %s)"
            cursor.executemany(insert_query, genre_movie_data)
            db.commit()

        driver.execute_script("arguments[0].click();", genre_button)
        time.sleep(3)
    except Exception as e:
        print(f"Skipping genre {genre} due to error: {e}")
        continue

cursor.close()
db.close()
driver.quit()
