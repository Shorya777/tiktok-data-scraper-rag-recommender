from datetime import datetime
from typing import Optional
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_classic.chains import RetrievalQA
from pathlib import Path
from src.prediction_scripts.data_models import RecommendationResponse
from utility.utilities import load_config, load_api_credentials

class llmRecommendation:
    def __init__(self, vector_db_path: str ,  openai_api_key: str, base_url: str):
        self.openai_api_key = openai_api_key
        self.base_url = base_url
        self.embeddings = OpenAIEmbeddings(api_key=openai_api_key, base_url=self.base_url)
        self.llm = ChatOpenAI(
            model="openai/gpt-oss-20b:free",
            base_url="https://openrouter.ai/api/v1",
            api_key=openai_api_key
            
            # temperature=0.7,
            # openai_api_key=openai_api_key
        )
        self.vector_db_path= vector_db_path
        self.vectorstore = None
        self.qa_chain = None
        self.last_update = None

    def get_vectorstore(self):
        self.vectorstore = Chroma(persist_directory=self.vector_db_path, embedding_function=self.embeddings)

    def create_qa_chain(self):
        """Create QA chain with custom prompt"""
        
        template = """You are a TikTok content strategy expert helping creators maximize their reach and engagement.

                    CONTEXT FROM CURRENT TRENDING DATA:
                    {context}
                    
                    CREATOR'S QUESTION: {question}
                    
                    Provide a strategic, actionable response that includes:
                    1. **Trending Analysis**: What's hot right now based on the data
                    2. **Content Recommendations**: Specific hashtags, songs, or themes to use
                    3. **Engagement Tactics**: Why these trends work (based on likes/comments)
                    4. **Action Items**: Clear next steps for the creator
                    
                    Be specific, cite engagement numbers, and reference actual trending items from the context.
                    Keep the tone encouraging and practical.
                    
                    STRATEGIC RECOMMENDATION:"""
        
        prompt = PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )
        
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vectorstore.as_retriever(
                search_type="mmr",  # Maximal Marginal Relevance for diversity
                search_kwargs={
                    "k": 6,
                    "fetch_k": 20
                }
            ),
            return_source_documents=True,
            chain_type_kwargs={"prompt": prompt}
        )
        
        print("✓ QA chain configured")

    def initialize(self):
        print("\n🚀 Initialize the RAG LLM..")
        print("Loading VectorDB")
        self.get_vectorstore()
        print("VectorDB Loaded")
        print("Creating QA  Chain")
        self.create_qa_chain()
        print("QA Chain Created")
        
        self.last_update = datetime.now()
        print(f"✅ LLM Ready! Last updated: {self.last_update}\n")

    def get_recommendation(
        self, 
        question: str, 
        # niche: Optional[str] = None
    ) -> RecommendationResponse:
        """Get AI recommendation for creator"""
        
        if not self.qa_chain:
            raise ValueError("System not initialized")
        
        enhanced_query = question
        # if niche:
        #     enhanced_query = f"[{niche.upper()} NICHE] {question}"
        
        result = self.qa_chain({"query": enhanced_query})
        
        sources = []
        trending_items = []
        
        for doc in result.get('source_documents', []):
            source_info = {
                'item': doc.metadata.get('item'),
                'type': doc.metadata.get('type'),
                # 'likes': doc.metadata.get('likes'),
                # 'engagement_score': doc.metadata.get('engagement_score')
            }
            sources.append(source_info)
            
            if source_info not in trending_items:
                trending_items.append(source_info)
        
        # Sort by engagement
        # trending_items.sort(key=lambda x: x['engagement_score'], reverse=True)
        
        return RecommendationResponse(
            answer=result['result'],
            trending_items=trending_items[:5],
            sources=sources,
            timestamp=datetime.now().isoformat()
        )

if __name__ == "__main__":
    config_file = Path("config.yaml");
    config= load_config(config_file)

    vector_db_path = config["path"]["vector_db"]
    openai_api_key, openai_base_url  = load_api_credentials()

    llmr = llmRecommendation(vector_db_path, openai_api_key, openai_base_url)
    llmr.initialize()

    question = "Which hashtag is the trending on TikTok related to gaming right now?"
    print("\n🤖 Generating recommendation...\n")
    response = llmr.get_recommendation(question)
    print(response)
