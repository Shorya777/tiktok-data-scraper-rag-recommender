import time
import csv
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pathlib import Path
from seleniumbase import Driver

from utility.utilities import load_driver, load_cookies, save_data, load_config

class scrapeSongs:    
    def __init__(self, url: str, cookie_file_path: Path, past_7_day_songs_path: Path, past_30_day_songs_path: Path):
        self.url = url
        self.cookie_file = cookie_file_path
        self.past_7_days= past_7_day_songs_path
        self.past_30_days = past_30_day_songs_path

    def switch_7_to_30_days(self, driver):
        try:
            dropdown = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div/main/div[2]/div/div[1]/div[3]/div[1]/div[1]/span/span'))
            )
            dropdown.click()
            time.sleep(1)
            
            option_30 = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'Last 30 days')]"))
            )
            option_30.click()
            time.sleep(5)
        except Exception as e:
            print("⚠️ Could not switch to 30 days:", e)
    
    def scroll_until_loaded(self, driver, pause=2, offset=200):
        last_height = driver.execute_script("return document.body.scrollHeight")

        while True:
            # scroll to slightly above the bottom
            driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight - {offset});")

            time.sleep(pause)

            new_height = driver.execute_script("return document.body.scrollHeight")

            if new_height == last_height:  # no new content loaded
                break
            last_height = new_height

        print("✅ Finished scrolling, all content loaded.")

    def scrape_trending_songs(self, driver):
        songs_data = []
        song_cards = driver.find_elements(By.CLASS_NAME, "ItemCard_soundItemContainer__GUmFb")  
        print(f"{len(song_cards)} songs found")
        for card in song_cards:
            try:
                song_name = card.find_element(By.CLASS_NAME, "ItemCard_musicName__2znhM").text
            except:
                hashtag_name = ""
            try:
                artist = card.find_element(By.CLASS_NAME, "ItemCard_autherName__gdrue").text
            except:
                artist = ""

            songs_data.append({
                "song": song_name.strip(),
                "artist": artist.strip()
            })
            
        return songs_data
        
    def collecting_song_data(self):
        driver = load_driver()
        driver.get(self.url)
        load_cookies(driver, self.cookie_file)
        driver.refresh()
        time.sleep(5)

        self.scroll_until_loaded(driver, pause= 3, offset=1200)
        
        songs_data_past_7_days = self.scrape_trending_songs(driver)
        save_data(self.past_7_days, songs_data_past_7_days) 
        
        driver.execute_script("window.scrollTo(0, 200);")
        self.switch_7_to_30_days(driver)    
        self.scroll_until_loaded(driver, pause= 3, offset=1200)

        songs_data_past_30_days = self.scrape_trending_songs(driver)
        save_data(self.past_30_days, songs_data_past_30_days)
        
        driver.quit()

if __name__ == "__main__":
    config_file = Path("config.yaml");
    config= load_config(config_file)

    path7 = Path(config["path"]["songs"]["past_7_days"])
    path30 = Path(config["path"]["songs"]["past_30_days"])
    path_creative_center = Path(config["path"]["cookies"]["tiktok_creative_center"])
    url_creative_center = config["url"]["tiktok_creative_center"]["song"]

    scrape_obj = scrapeSongs(url= url_creative_center, cookie_file_path= path_creative_center , past_7_day_songs_path= path7, past_30_day_songs_path= path30)
    scrape_obj.collecting_song_data()



