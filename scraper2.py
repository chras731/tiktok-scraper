import time
import re
import csv
import os
import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# TikTok Credentials: This is just here so I can copy paste
USERNAME = "rise.beautycosmetics@gmail.com"
PASSWORD = "RiseTest1!"

SEARCH_TERMS = ["Wonyoung Lips", "Glass Skin"]

MAX_VIDEOS = 2000

CSV_FILENAME = "tiktok_video_data.csv"

def setup_driver():
    """Set up Selenium WebDriver with Chrome."""
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")  
    options.add_argument("--disable-blink-features=AutomationControlled")  
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def extract_timestamp(video_url):
    """Extract timestamp from a TikTok video URL"""
    match = re.search(r"video/(\d+)", video_url)
    if not match:
        return None  # Invalid URL format

    tagNo = int(match.group(1))  # Convert extracted ID to integer
    timestamp = tagNo >> 32  # Shift right 32 bits to extract left-most 32 bits
    dt = datetime.datetime.utcfromtimestamp(timestamp)  # Convert to datetime
    return dt

def filter_by_date(timestamp, filter_choice):
    """Filters videos based on user choice"""
    today = datetime.datetime.utcnow()
    
    if filter_choice == "1":  # Last week
        cutoff = today - datetime.timedelta(weeks=1)
    elif filter_choice == "2":  # Last 2 weeks
        cutoff = today - datetime.timedelta(weeks=2)
    elif filter_choice == "3":  # Last month (approx 30 days)
        cutoff = today - datetime.timedelta(days=30)
    else:
        return True  # No filter applied

    return timestamp >= cutoff

def login_tiktok(driver):
    """Logs into TikTok manually."""
    driver.get("https://www.tiktok.com/login")
    print("Please log in manually. Press Enter once logged in.")
    input()  # Wait for user confirmation
    time.sleep(5)

def search_tiktok(driver, query, filter_choice):
    """Performs a TikTok search and collects video URLs with timestamps."""
    print(f"Searching for: {query}")
    search_url = f"https://www.tiktok.com/search?q={query.replace(' ', '%20')}"
    driver.get(search_url)
    time.sleep(5)

    video_data = []
    last_height = driver.execute_script("return document.body.scrollHeight")

    while len(video_data) < MAX_VIDEOS:
        video_links = driver.find_elements(By.XPATH, "//a[contains(@href, '/video/')]")
        for link in video_links:
            url = link.get_attribute("href")
            if url and url not in [v["url"] for v in video_data]:  # Avoid duplicates
                timestamp = extract_timestamp(url)
                if timestamp and filter_by_date(timestamp, filter_choice):  # Apply filter
                    video_data.append({
                        "keyword": query,
                        "url": url,
                        "date": timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')
                    })
                
                if len(video_data) >= MAX_VIDEOS:
                    break

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        new_height = driver.execute_script("return document.body.scrollHeight")
        
        if new_height == last_height:
            break  # Stop if we can't scroll further
        last_height = new_height

    print(f"Collected {len(video_data)} videos for '{query}' (Filtered by: {filter_choice})")
    
    # Append results immediately to CSV
    save_to_csv(video_data)

def save_to_csv(video_data):
    """Save video data to a CSV file, appending results after every keyword search."""
    if not video_data:
        return  # Skip if no data is available after filtering

    file_exists = os.path.isfile(CSV_FILENAME)  # Check if file exists

    with open(CSV_FILENAME, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["keyword", "url", "datetime"])

        if not file_exists:
            writer.writeheader()  # Write header only if the file is new

        writer.writerows(video_data)
    
    print(f"Saved {len(video_data)} new entries to '{CSV_FILENAME}'")

def main():
    print("Choose a date filter for TikTok videos:")
    print("1 - Only videos from the last week")
    print("2 - Only videos from the last 2 weeks")
    print("3 - Only videos from the last month")
    print("4 - No filter (include all videos)")
    filter_choice = input("Enter your choice (1/2/3/4): ").strip()

    if filter_choice not in ["1", "2", "3", "4"]:
        print("Invalid choice. Defaulting to no filter.")
        filter_choice = "4"

    driver = setup_driver()
    login_tiktok(driver)

    for term in SEARCH_TERMS:
        search_tiktok(driver, term, filter_choice)

    driver.quit()

if __name__ == "__main__":
    main()
