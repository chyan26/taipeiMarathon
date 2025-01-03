


import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

# Set up Selenium WebDriver with Chrome
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in headless mode (no browser window)
chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration for headless

# Use WebDriverManager to automatically manage the ChromeDriver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# Base URL with pagenum as a placeholder
base_url = 'https://www.championchiptw.com/report/report_w.php?EventCode=20241215&Race=MA&sn=&Sex=N&CatId=0&pagenum={}'

# Initialize a list to store extracted data
all_data = []

# Loop through all 17 pages
for page_num in range(1, 18):  # Page numbers from 1 to 17
    # Construct the URL for the current page
    url = base_url.format(page_num)
    
    # Open the page
    driver.get(url)
    
    # Wait for the page to load (you can adjust the time if necessary)
    time.sleep(3)  # Sleep for 3 seconds
    
    # Find all rows in the table that contain the relevant data
    rows = driver.find_elements(By.XPATH, "//tr[td[@class='OL'] or td[@class='EL']]")
    
    # Extract the required fields from each row
    for row in rows:
        bibnr = row.find_element(By.XPATH, ".//td[1]").text.strip()  # Bib number
        name = row.find_element(By.XPATH, ".//td[2]").text.strip()  # Name
        category = row.find_element(By.XPATH, ".//td[4]").text.strip()  # Category
        official_time = row.find_element(By.XPATH, ".//td[5]").text.strip()  # Official Time
        rank_all = row.find_element(By.XPATH, ".//td[6]").text.strip()  # Rank All
        net_time = row.find_element(By.XPATH, ".//td[8]").text.strip()  # Net Time
        
        # Append the extracted data as a dictionary
        all_data.append({
            "Bib Number": bibnr,
            "Name": name,
            "Category": category,
            "Official Time": official_time,
            "Rank All": rank_all,
            "Net Time": net_time
        })

    print(f"Extracted data from page {page_num}")

# Convert the data to a pandas DataFrame
df = pd.DataFrame(all_data)

# Save the DataFrame to a CSV file
df.to_csv("race_results.csv", index=False, encoding="utf-8-sig")

print("Data has been saved to 'race_results.csv'.")

# Close the browser
driver.quit()
