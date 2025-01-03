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
from requests.exceptions import HTTPError
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException


class MarathonCrawler:
    def __init__(self, data_dir='data'):
        self.driver = self.init_driver()
        self.data_dir = data_dir
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def init_driver(self):
        options = uc.ChromeOptions()
        options.headless = False
        driver = uc.Chrome(options=options)
        return driver

    def check_existing_data(self, bib_number):
        file_path = os.path.join(self.data_dir, f'{bib_number}.json')
        return os.path.exists(file_path)

    def load_existing_data(self, bib_number):
        file_path = os.path.join(self.data_dir, f'{bib_number}.json')
        with open(file_path, 'r') as f:
            return json.load(f)

    def save_data(self, bib_number, data):
        file_path = os.path.join(self.data_dir, f'{bib_number}.json')
        with open(file_path, 'w') as f:
            json.dump(data, f)

    def scrape_runner_data(self, url, bib_number, timeout=10):
        if self.check_existing_data(bib_number):
            print(f"Data for bib number {bib_number} already exists. Skipping scraping.")
            return self.load_existing_data(bib_number)

        try:
            # Open the URL
            self.driver.get(url)
            
            # Wait for the page to load
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'rank-card-athlete-name'))
            )
            time.sleep(2)  # Ensure page is fully loaded

            # Parse the page source
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')

            # Extract runner information
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
        except HTTPError as http_err:
            if response.status_code == 404:
                print(f"Error: Runner with bib number {bib_number} not found (404).")
            else:
                print(f"HTTP error occurred: {http_err}")
        except Exception as e:
            print(f"Error scraping bib number {bib_number}: {e}")
            return None

    def close_driver(self):
        self.driver.quit()


def fetch_bib_data(base_url, bib_number, crawler):
    url = f"{base_url}{bib_number}"
    try:
        return crawler.scrape_runner_data(url, bib_number)
    except HTTPError as http_err:
        if http_err.response.status_code == 404:
            print(f"404 error encountered for URL: {url}. Skipping...")
            return None
        else:
            print(f"HTTP error occurred: {http_err}")
            raise
    except NoSuchElementException as e:
        print(f"Element not found for bib number {bib_number}: {e}")
        return None
    except TimeoutException as e:
        print(f"Timeout occurred for bib number {bib_number}: {e}")
        return None
    except WebDriverException as e:
        print(f"WebDriver error occurred for bib number {bib_number}: {e}")
        return None
    except Exception as e:
        print(f"Other error occurred for bib number {bib_number}: {e}")
        return None


def loop_through_bibs(base_url, output_file):
    crawler = MarathonCrawler()
    
    full_marathon_ranges = [
    (1001, 1600),
    #(2001, 2700),
    #(3001, 3700),
    #(4001, 4700),
    #(5001, 5800),
    #(6001, 6800),
    #(7001, 7700),
    #(8001, 8800),
    #(9001, 9800),
    #(10001, 10800),
    #(11001, 11800),
    #(12001, 12800),
    #(13001, 13700)
    ]
    
    try:
        all_data = []
        bib_numbers = [
            f"{bib:06d}"
            for start, end in full_marathon_ranges
            for bib in range(start, end + 1)
]

        max_workers = 5  # Adjust based on your system
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_bib = {executor.submit(fetch_bib_data, base_url, bib, crawler): bib for bib in bib_numbers}

            for future in as_completed(future_to_bib):
                bib = future_to_bib[future]
                try:
                    data = future.result()
                    if data:
                        all_data.append(data)
                except Exception as e:
                    print(f"Error fetching bib number {bib}: {e}")

        with open(output_file, 'w') as json_file:
            json.dump(all_data, json_file, indent=4, ensure_ascii=False)
        print(f"All data saved to {output_file}")
    finally:
        crawler.close_driver()


# Convert JSON data to DataFrame
def json_to_dataframe(json_file):
    with open(json_file, 'r') as file:
        data = json.load(file)

    records = []
    for entry in data:
        runner_info = entry['runner_info']
        record = entry['record']

        # Extract HM Time from cpid = 5
        hm_time = None
        if 'cp' in record and '5' in record['cp']:
            hm_time = record['cp']['5'].get('raceTime')

        records.append({
            'Bib Number': runner_info.get('Bib Number'),
            'Name': runner_info.get('Name'),
            'Group': runner_info.get('Group'),
            'Gender': runner_info.get('Gender'),
            'Net Time': runner_info.get('Net Time'),
            'HM Time': hm_time
        })

    df = pd.DataFrame(records)
    return df


# Base URL and output file
base_url = 'https://www.bravelog.tw/athlete/1189/'
output_file = 'all_runner_data.json'

loop_through_bibs(base_url, output_file)

# Convert JSON data to DataFrame
df = json_to_dataframe(output_file)
df.to_csv('2025_tpe_marathon.csv', index=False)
