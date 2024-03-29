import asyncio
from multiprocessing import Pool
import httpx
import logging
import os
from datetime import datetime
import lxml.html as html
import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import warnings
import requests
import json
import ndjson
warnings.filterwarnings("ignore")

class SeleniumScraper:
    def __init__(self, timeout=10):
        self.timeout = timeout
        self.session = httpx.AsyncClient(timeout=self.timeout)
        self.stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.storagePath = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "../Data/"
        )

        logging.basicConfig(
            filename=self.storagePath + "logs/Scraper_{}.log".format(self.stamp),
            level=logging.INFO,
            filemode="w",
        )
        self.headers = {
            'authority': 'www.amazon.com',
            'pragma': 'no-cache',
            'cache-control': 'no-cache',
            'dnt': '1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.79 Safari/537.36',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'sec-fetch-site': 'none',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-dest': 'document',
            'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        }

    async def fetch_request_async(self, url, params=None):
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36"
            }
            response = await self.session.get(url, headers=headers)
    
            if response.status_code == 200:
                print("Response status code successful for url: {} and status code: {}".format(url, 200))
                return response.text
            
            if response.status_code == 301:
                # retry with redirect
                response = await self.session.get(response.headers['Location'])
                response.raise_for_status()
                if response.status_code == 200:
                    return response.text
                
        except Exception as e:
            logging.info(
                "Exception occurred for url: {} and exception: {}".format(url, e)
            )
            pass
            return None
    
    def fetch_request_normal(self, url, params=None):
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36"
            }
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                print("Response status code successful for url: {} and status code: {}".format(url, 200))
                return response.text
            
            if response.status_code == 301:
                # retry with redirect
                response = requests.get(response.headers['Location'])
                response.raise_for_status()
                if response.status_code == 200:
                    return response.text
            
        except Exception as e:
            logging.info(
                "Exception occurred for url: {} and exception: {}".format(url, e)
            )
            pass
            return None
        
    def get_xpath_link(self, doc, xpath, website):
        try:
            name = doc.xpath("".join(xpath))
            for i in range(len(name)):
                if name[i].startswith("/"):
                    name[i] = website + name[i]
                else:
                    name[i] = name[i]
            return name

        except Exception as e:
            logging.info("Error in getting {}: {}".format(name, e))
            pass
            return None
            pass
        
    def get_selenium_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-logging")
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument("--silent")
        chrome_options.add_argument("--blink-settings=imagesEnabled=false")
        driver = webdriver.Chrome(chrome_options=chrome_options)
        return driver

    def fetch_request_selenium(self, url, waiting_time=1):
        try:
            driver = self.get_selenium_driver()
            driver.get(url)
            time.sleep(waiting_time)
            doc = html.fromstring(driver.page_source)
            logging.info("Response status code successful for url: {} and status code: {}".format(url, 200))
            driver.close()
            return doc

        except Exception as e:
            logging.info(
                "Exception occurred for url: {} and exception: {}".format(url, e)
            )
            pass

    def get_xpath_data(self, doc, xpath):
        try:
            name = doc.xpath(xpath)
            return name

        except Exception as e:
            print("Error in getting {}: {}".format(name, e))
            pass
            return None
        
    def slow_page_scroll(self, driver, speed):
        current_scroll_position = driver.execute_script("return window.pageYOffset;")
        while current_scroll_position < driver.execute_script(
            "return document.body.scrollHeight;"
        ):
            driver.execute_script(
                "window.scrollTo(0, arguments[0]);", current_scroll_position
            )
            current_scroll_position += 1000
            time.sleep(speed)

    def data_storage(self, df_list, unique_id, name):
        df_combined = pd.concat(df_list, ignore_index=True)
        df_combined.drop_duplicates(subset=unique_id, inplace=True)
        df_combined.to_csv(
            self.storagePath + "raw/" + "{}_{}.csv".format(name, self.stamp),
            index=False,
        )
      
    def cleanData(self, array):
        array = [x.strip() for x in array]
        array = list(filter(None, array))
        array = [x.encode("ascii", "ignore").decode() for x in array]
        array = [x.replace("\n", "") for x in array]
        return array
    
    