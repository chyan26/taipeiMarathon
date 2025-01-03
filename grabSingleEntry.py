from concurrent.futures import ThreadPoolExecutor, as_completed
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import os
import json
import time
import pandas as pd
import requests
from threading import local


class MarathonCrawler:
    def __init__(self, data_dir='data'):
        self.driver = self.init_driver()
        self.session = None  # To hold the requests session after bypassing Cloudflare
        self.data_dir = data_dir
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def init_driver(self):
        options = uc.ChromeOptions()
        options.headless = False
        driver = uc.Chrome(options=options)
        return driver

    def init_session(self):
        # Use driver to bypass Cloudflare
        self.driver.get('https://example.com')  # Replace with target URL
        WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))

        # Extract session details
        self.session = self.get_session_from_driver()

        # Optionally close the driver if no longer needed
        self.driver.quit()

    def get_session_from_driver(self):
        """Extract cookies and headers from Selenium driver."""
        session = requests.Session()
        # Extract cookies
        for cookie in self.driver.get_cookies():
            session.cookies.set(cookie['name'], cookie['value'])
        # Extract headers (optional, as some headers are added by default by `requests`)
        session.headers.update({
            "User-Agent": self.driver.execute_script("return navigator.userAgent;"),
        })
        return session

    def check_existing_data(self, bib_number):
        file_path = os.path.join(self.data_dir, f'{bib_number}.json')
        return os.path.exists(file_path)

    def load_existing_data(self, bib_number):
        file_path = os.path.join(self.data_dir, f'{bib_number}.json')
        with open(file_path, 'r') as file:
            return json.load(file)

    def save_data(self, bib_number, data):
        file_path = os.path.join(self.data_dir, f'{bib_number}.json')
        with open(file_path, 'w') as f:
            json.dump(data, f)

    def fetch_with_requests(self, url):
        """Fetch a URL using the initialized requests session."""
        if not self.session:
            raise RuntimeError("Session not initialized. Call `init_session()` first.")
        response = self.session.get(url)
        response.raise_for_status()
        return response.text

    def scrape_data(self, bib_number):
        """Example method to scrape data using requests."""
        if self.check_existing_data(bib_number):
            print(f"Data for bib {bib_number:06d} already exists. Loading from file.")
            return self.load_existing_data(bib_number)

        url = f"https://www.bravelog.tw/athlete/1189/{bib_number}"  # Replace with actual URL structure
        html = self.fetch_with_requests(url)

        # Parse the HTML using BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        data = self.parse_data(soup, bib_number)

        # Save data to file
        file_path = os.path.join(self.data_dir, f'{bib_number}.json')
        with open(file_path, 'w') as file:
            json.dump(data, file)

        return data

    def parse_data(self, soup, bib_number):
        """Parse the BeautifulSoup object to extract marathon runner data."""
        try:
            runner_info = {'Bib Number': bib_number}
            name_div = soup.find('div', class_='flex justify-content-between rank-card-athlete-name')
            if name_div:
                name_h1 = name_div.find('h1', class_='fc-white float-left my-auto')
                if name_h1:
                    runner_info['Name'] = name_h1.get_text(strip=True)
            
            # Other details
            info_div = soup.find('div', class_='flex text-align-left rank-card-detial float-left')
            if info_div:
                spans = info_div.find_all('span', class_='fs-1')
                if len(spans) >= 4:
                    runner_info['Event'] = spans[0].get_text(strip=True)
                    runner_info['Group'] = spans[1].get_text(strip=True)
                    runner_info['Nation'] = spans[2].get_text(strip=True)
                    runner_info['Gender'] = spans[3].get_text(strip=True)

            official_time_p = soup.find('p', class_='rankCard-text text-align-left grade')
            if official_time_p:
                runner_info['Gun Time'] = official_time_p.get_text(strip=True)

            net_time_p = soup.find('p', class_='rankCard-text main-color text-align-left grade')
            if net_time_p:
                runner_info['Net Time'] = net_time_p.get_text(strip=True)

            # JavaScript variable `record`
            script_tag = soup.find('script', string=lambda t: t and "var record =" in t)
            if script_tag:
                script_content = script_tag.string
                start_index = script_content.find("var record =") + len("var record =")
                end_index = script_content.find("};", start_index) + 1
                raw_json = script_content[start_index:end_index].strip()
                data = json.loads(raw_json)

                # Modify CPAccumulate
                if "cp" in data:
                    for cp_id, cp_data in data["cp"].items():
                        if cp_id.isdigit() and int(cp_id) > 4:
                            cp_data["CPAccumulate"] -= 5780

                result = {'runner_info': runner_info, 'record': data}
                self.save_data(bib_number, result)
                return result
            else:
                print(f"'var record' not found for bib number {bib_number}")
            return None
        
        except Exception as e:
            print(f"Error scraping bib number {bib_number}: {e}")
            return None

if __name__ == "__main__":
    crawler = MarathonCrawler()
    crawler.init_session()  # Initialize session by bypassing Cloudflare

    
    # Example usage
    bib_number = '013724'
    data = crawler.scrape_data(bib_number)
    #print(data)
