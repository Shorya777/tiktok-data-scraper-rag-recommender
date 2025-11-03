from src.scraping_scripts.tiktok_creative_center.scrape_hashtags import scrapeHashtags
from src.scraping_scripts.tiktok_creative_center.scrape_songs import scrapeSongs
from src.scraping_scripts.tiktok_creative_center.merge_data import merge
from src.scraping_scripts.tiktok.tiktok_comments import scrapeComments
from src.prediction_scripts.create_vector_db import createVectorDB
from src.prediction_scripts.rag_llm import llmRecommendation
from utility.utilities import load_config, load_api_credentials
from pathlib import Path

class tikTokRagPlatform:
    def __init__(self,hashtag_url: str, song_url: str, tiktok_url: str , base_url: str,
                 creative_center_cookie_file_path: Path, tiktok_cookie_file_path: Path,
                 past_7_day_songs_path: Path, past_30_day_songs_path: Path, past_7_day_hashtags_path: Path,
                 past_30_day_hashtags_path: Path, merged_data_path_hashtag: Path, merged_data_path_song: Path,
                 comment_output_folder_hashtag: Path, comment_output_folder_song: Path, vector_db_path: str, openai_api_key: str, if_hash: bool):
        
        self.comment_output_folder = comment_output_folder_hashtag if if_hash else comment_output_folder_song
        self.sh = scrapeHashtags(hashtag_url, creative_center_cookie_file_path, 
                                 past_7_day_hashtags_path, past_30_day_hashtags_path)
        self.ss = scrapeSongs(song_url, creative_center_cookie_file_path, 
                              past_7_day_songs_path, past_30_day_songs_path)
        self.m = merge(past_7_day_hashtags_path, past_30_day_hashtags_path, merged_data_path_hashtag,
                       past_7_day_songs_path, past_30_day_songs_path,  merged_data_path_song)
        self.sc = scrapeComments(tiktok_url, merged_data_path_hashtag, merged_data_path_song,
                                 self.comment_output_folder , tiktok_cookie_file_path, if_hash)
        self.cvdb = createVectorDB(self.comment_output_folder, vector_db_path,  openai_api_key, base_url, if_hash)
        self.llmr = llmRecommendation(vector_db_path, openai_api_key, base_url)

    def scrape_hashtag_process(self):
        self.sh.collecting_hashtag_data()

    def scrape_song_process(self):
        self.ss.collecting_song_data()
     
    def merge_hashtag_and_song_process(self):
        self.m.merge()

    def scrape_comments_process(self):
        self.sc.collecting_comments()

    def generate_vector_db(self):
        self.cvdb.initialize()

    def generate_response(self, question: str):
        self.llmr.initialize()
        response = self.llmr.get_recommendation(question)
        return response

def main():
    # Loading all configurations
    config_file = Path("config.yaml");
    config= load_config(config_file)

    creative_center_cookie_file_path = Path(config["path"]["cookies"]["tiktok_creative_center"])
    tiktok_cookie_file_path = Path(config["path"]["cookies"]["tiktok"])

    past_7_day_hashtags_path= Path(config["path"]["hashtags"]["past_7_days"])
    past_30_day_hashtags_path= Path(config["path"]["hashtags"]["past_30_days"])
    hashtag_url = config["url"]["tiktok_creative_center"]["hashtag"]

    past_7_day_songs_path= Path(config["path"]["songs"]["past_7_days"])
    past_30_day_songs_path= Path(config["path"]["songs"]["past_30_days"])
    song_url = config["url"]["tiktok_creative_center"]["song"]

    merged_data_path_hashtag = Path(config["path"]["merge"]["hashtag"])
    merged_data_path_song = Path(config["path"]["merge"]["song"])
    tiktok_cookie_file_path = Path(config["path"]["cookies"]["tiktok"])
    tiktok_url = config["url"]["tiktok"]
    comment_output_folder_hashtag = Path(config["path"]["comments_data"]["hashtags"])
    comment_output_folder_song = Path(config["path"]["comments_data"]["songs"])
    
    vector_db_path = config["path"]["vector_db"]
    openai_api_key, base_url = load_api_credentials()
    if_hash = 1 # 0 = song, 1 = hashtag 
    
    #Scraping and Generating response user query
    platform_obj = tikTokRagPlatform(hashtag_url, song_url, tiktok_url, base_url,
                     creative_center_cookie_file_path, tiktok_cookie_file_path,
                     past_7_day_songs_path, past_30_day_songs_path, past_7_day_hashtags_path,
                     past_30_day_hashtags_path, merged_data_path_hashtag, merged_data_path_song,
                     comment_output_folder_hashtag, comment_output_folder_song, vector_db_path, openai_api_key, if_hash)

    platform_obj.scrape_hashtag_process()
    platform_obj.scrape_song_process()
    platform_obj.merge_hashtag_and_song_process()
    platform_obj.scrape_comments_process()
    platform_obj.generate_vector_db()

    question = "Which hashtag is the trending on TikTok related to gaming right now?"
    print("\n🤖 Generating recommendation...\n")
    response = platform_obj.generate_response(question)
    print(response)

if __name__ == "__main__":
    main()
