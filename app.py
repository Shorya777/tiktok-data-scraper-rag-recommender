import streamlit as st
from utility.utilities import load_config, load_api_credentials
from pathlib import Path
from main import tikTokRagPlatform

st.set_page_config(page_title="TikTok RAG Recommender", layout="wide")

st.title("🎯 TikTok Trend Intelligence (RAG)")

query = st.text_input("Ask a question about TikTok trends:")

if st.button("Generate Recommendation"):
    with st.spinner("Thinking..."):
        # TODO: Call your RAG pipeline here

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
        response = platform_obj.generate_response(query)


        # Render formatted markdown directly
        st.markdown(response.answer)
