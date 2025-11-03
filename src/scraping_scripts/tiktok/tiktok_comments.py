import time
import json
import csv
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pathlib import Path
import pandas as pd
import os
from seleniumbase import Driver
from utility.utilities import load_config, load_driver, load_cookies

class scrapeComments:
    def __init__(self, url: str, hashtag_data_path: Path, song_data_path: Path, output_folder: Path, cookie_file: Path, if_hash: bool):
        self.url = url
        self.hashtag_data_path= hashtag_data_path
        self.song_data_path= song_data_path
        self.output_folder = output_folder
        self.cookie_file= cookie_file
        self.if_hash = if_hash

    def search_keyword(self, driver, keyword: str):
        search = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div[2]/div[1]/div/div[2]/div[2]'))
        )
        search.click()
        search_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div[2]/div[1]/div/div[5]/div[1]/div[2]/form/input'))
        )
        search_input.send_keys(Keys.CONTROL + "a")
        search_input.send_keys(Keys.DELETE)
        time.sleep(0.5)
        search_input.send_keys(keyword)
        search_input.send_keys(Keys.ENTER)



    def scrape_comments_per_keyword(self, driver):    
        initial_elements= driver.find_elements(
            By.CSS_SELECTOR,
            "div.css-vb7jd0-5e6d46e3--DivItemContainerForSearch a.css-143ggr2-5e6d46e3--AVideoContainer")[0:3]
        num_elements = len(initial_elements)
        results = []
        for i in range(num_elements):
            # Re-find elements in each iteration to avoid StaleElementReferenceException
            current_elements = driver.find_elements(
                By.CSS_SELECTOR,
                "div.css-vb7jd0-5e6d46e3--DivItemContainerForSearch a.css-143ggr2-5e6d46e3--AVideoContainer")[0:3]
            
            if i < len(current_elements):
                element = current_elements[i]
                url = element.get_attribute('href')
                
                element_text = element.text
                print(f"Clicking element: {element_text}")
                try:
                    top_comments = []
                    element.click()
                    time.sleep(5)
                    print(f"Navigated to: {driver.current_url}")
                    text_ele = driver.find_elements(By.XPATH, '/html/body/div[1]/div[2]/div[2]/div[1]/div[2]/div[3]/div/div[2]/div[1]/div/div[1]/div[1]/div[2]/div[1]/div/div[2]/div/span[1]')
                    caption = text_ele[0].text if text_ele else ""
                    likes = driver.find_element(By.CLASS_NAME, "css-p4azz9-5e6d46e3--StrongText").text.strip()
                    try: 
                        song_ele = driver.find_element(By.XPATH, '/html/body/div[1]/div[2]/div[2]/div[1]/div[2]/div[3]/div/div[2]/div[1]/div/div[1]/div[1]/div[2]/h4/a/div')
                        video_song = song_ele.text    
                    except:
                        print("Song not found for this video")
                        video_song = "Not Mentioned"
                    comments_ele = driver.find_elements(By.CLASS_NAME, "css-xdyzh5-5e6d46e3--PCommentText")[:5]
                    for comment in comments_ele:
                        comment_span = comment.find_element(By.TAG_NAME, "span")
                        top_comments.append(comment_span.text)
                        
                    rec = {
                        "caption": caption,
                        "video_url": url,
                        "likes": likes,
                        "video_song": video_song,
                        "comments": top_comments,
                    }
                    print(rec)
                    results.append(rec)
                    
                    driver.back()
                    time.sleep(2)
                    print(f"Navigated back to: {driver.current_url}")
                    print("*"*30)
                    
                except Exception as e:
                    print(f"Error clicking element {element_text}: {e}")
                    
        return results


    def collecting_comments(self):
        driver = load_driver()
        url = self.url 
        driver.get(url)
        load_cookies(driver, self.cookie_file)
        driver.refresh()
        time.sleep(5)
        if(self.if_hash):
            df = pd.read_csv(self.hashtag_data_path)
        else:
            df = pd.read_csv(self.song_data_path)

        for idx, row in df.iterrows():
            if(idx == 10):
                break
            print(f"ITERATION: {idx}")
            if self.if_hash:
                hashtag = row['hashtag']
                hashtag = hashtag.replace(' ', '')
                self.search_keyword(driver, hashtag)
                time.sleep(5)
                path = os.path.join(self.output_folder, f"{hashtag}.json")
                
            else : 
                song = row['song']
                song = song.replace(' ', '')
                self.search_keyword(driver, song)
                time.sleep(5)
                path = os.path.join(self.output_folder,  f"{song}.json")
                
            results = self.scrape_comments_per_keyword(driver)
            if(self.if_hash):
                if(pd.isnull(row['post_no_30days'])):
                    past_30_days = "NULL"
                else:
                    past_30_days = row['post_no_30days']
                
                if(pd.isnull(row['post_no_7days'])):
                    past_7_days = "NULL"
                else:
                    past_7_days = row['post_no_7days']

            else:
                if(pd.isnull(row['artist_30days'])):
                    past_30_days = "NULL"
                else:
                    past_30_days = row['artist_30days']
                
                if(pd.isnull(row['artist_7days'])):
                    past_7_days = "NULL"
                else:
                    past_7_days = row['artist_7days']
            
            persistence_info = {"past_30_days": past_30_days, "past_7_days": past_7_days}
            results.append(persistence_info)

            with open(path, "w", encoding="utf8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            print(f"Saved {len(results)} video records to {path}")

if __name__ == "__main__":
    config_file = Path("config.yaml");
    config= load_config(config_file)

    hashtag_data_path = Path(config["path"]["merge"]["hashtag"])
    song_data_path = Path(config["path"]["merge"]["song"])
    output_data_path = Path(config["path"]["comment_data"]["hashtags"])
    cookie_file_path = Path(config["path"]["cookies"]["tiktok"])
    url = config["url"]["tiktok"]
    if_hash = 0
    sc_obj = scrapeComments(url, hashtag_data_path, song_data_path, output_data_path, cookie_file_path, if_hash)
    sc_obj.collecting_comments()
    

