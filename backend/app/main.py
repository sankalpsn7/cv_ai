from fastapi import FastAPI
from app.api.routes import router



app = FastAPI(
    title="AI resume analyser & ATS Assistant API",
    description="Production-ready backend for parsing, scoring, and querying CVs using Groq and local FAISS embeddings.",
    version="1.0.0"
)


app.include_router(router)


