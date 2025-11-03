import os
import json
from datetime import datetime
from typing import Dict, List, Optional
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.documents import Document
from pathlib import Path
from src.prediction_scripts.data_models import CreatorQuery, RecommendationResponse
from utility.utilities import load_config, load_api_credentials

class createVectorDB:
    def __init__(self, data_folder: Path, vector_db_path: str,  openai_api_key: str, base_url: str, if_hash: bool):
        self.data_folder = data_folder
        self.openai_api_key = openai_api_key
        self.vector_db_path = vector_db_path
        self.base_url = base_url
        self.embeddings = OpenAIEmbeddings(api_key=openai_api_key, base_url=self.base_url)
        self.llm = ChatOpenAI(
            model="openai/gpt-oss-20b:free",
            base_url="https://openrouter.ai/api/v1",
            api_key=openai_api_key
            
            # temperature=0.7,
            # openai_api_key=openai_api_key
        )
        self.if_hash = if_hash
        self.vectorstore = None
        self.last_update = None

    def extract_name_from_filename(self, filename: str) -> str:
        name = filename.replace('.json', '')
        
        return name;        
        
    def load_json_files(self) -> List[Dict]:
        documents = []
        for filename in os.listdir(self.data_folder):
            if filename.endswith('.json'):
                filepath = os.path.join(self.data_folder, filename)
                name = self.extract_name_from_filename(filename)
                try:
                    if(self.if_hash):
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            documents.append({
                                'hashtag': name,
                                'data': data,
                                'scraped_at': os.path.getmtime(filepath)
                            })
                    else:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            documents.append({
                                'song': name,
                                'data': data,
                                'scraped_at': os.path.getmtime(filepath)
                            })
                            
                except Exception as e:
                    print(f"Error loading {filename}: {e}")
        
        print(f"✓ Loaded {len(documents)} JSON files")
        return documents


    def extract_trending_items(self, json_data: List[Dict]) -> List[Dict]:
        """Extract and rank trending items by engagement"""
        trending = []
        
        for item in json_data:
            data = item['data']
            hashtag_or_song = item['hashtag'] or item['song']
            total_engagement =0
            for i in range(len(data)):
                if(data[i]["caption"]):
                    total_engagement+= data[i]["likes"]
            avg_engagement = total_engagement / len(data)
                    
            trending.append({
                'item': hashtag_or_song,
                'type': 'hashtag' if 'hashtag' in item else 'song',
                'video_count': len(data),
                'avg_engagement': avg_engagement,
                'top_caption': data[0].get('caption', '') if data[0]["caption"] else ''
            })
        
        trending.sort(key=lambda x: x['avg_engagement'], reverse=True)
        return trending
    
    def create_documents(self, json_data: List[Dict]) -> List[Document]:
        """Convert JSON to LangChain Documents with rich metadata"""
#        print(json_data)
#        print(self.data_folder) 
#       json_data[0]["data"][2]["caption"]
        documents = []
        
        for item in json_data:
            data = item['data']
            
            hashtag_or_song = item.get('hashtag') or item.get('song', 'Unknown')
            
            for i, d in enumerate(data):
                if "caption" in d:
                    video  = d
                else:
                    continue
                caption = video.get('caption', '')
                likes = video.get('likes', 0)
                comments = video.get('comments', [])
                
                content = f"""
                    🎯 TRENDING: {hashtag_or_song}
                    📝 Caption: {caption}
                    ❤️ Engagement: {likes:} likes
                    💬 Top Comments:
                    {chr(10).join(f"  - {c}" for c in comments[:3])}
                    
                    Content Type: {'Hashtag' if 'hashtag' in item else 'Song'}
                    """.strip()
                
                doc = Document(
                    page_content=content,
                    metadata={
                        'item': hashtag_or_song,
                        'type': 'hashtag' if 'hashtag' in data else 'song',
                        # 'video_rank': i + 1,
                        # 'comment_count': len(comments),
                    }
                )
                documents.append(doc)
        
        print(f"✓ Created {len(documents)} indexed documents")
        return documents
    
    def build_vectorstore(self, documents: List[Document]):
        """Build or update vector store"""
        self.vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            persist_directory=self.vector_db_path,
            collection_name="tiktok_trends"
        )
        print(f"✓ Vector store built with {len(documents)} documents")
    
    
    def initialize(self):
        print("\n🚀 Initialize Vector Database...")
        
        json_data = self.load_json_files()
        documents = self.create_documents(json_data)
        self.build_vectorstore(documents)
#        self.create_qa_chain()
        
        self.last_update = datetime.now()
        print(f"✅ Vector Database Created! Last updated: {self.last_update}\n")
    
    def update_from_new_scrape(self):
        """Call this after new data is scraped"""
        print("\n🔄 Updating platform with new data...")
        self.initialize()
    
    def get_stats(self) -> Dict:
        """Get platform statistics"""
        json_data = self.load_json_files()
        trending = self.extract_trending_items(json_data)
        
        return {
            'total_items_indexed': len(json_data),
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'top_5_trending': trending[:5]
        }

if __name__ == "__main__":
    config_file = Path("config.yaml");
    config= load_config(config_file)

    data_folder_path = Path(config["path"]["comments_data"]["hashtags"])
    vector_db_path = config["path"]["vector_db"]
    openai_api_key, openai_base_url  = load_api_credentials()
    if_hash = 1

    cvdb = createVectorDB(
        data_folder=data_folder_path,
        vector_db_path= vector_db_path,
        openai_api_key=openai_api_key,
        base_url = openai_base_url,
        if_hash =if_hash
    )
    cvdb.initialize()    
