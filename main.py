from fastapi import FastAPI
from llama_index.llms.openai import OpenAI
from llama_index.llms.anthropic import Anthropic
import chromadb
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="AI Project")

# Initialize LLMs
openai_llm = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
anthropic_llm = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Initialize ChromaDB
chroma_client = chromadb.PersistentClient(path="./chroma_db")

@app.get("/")
async def root():
    return {"message": "AI Project API is running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)