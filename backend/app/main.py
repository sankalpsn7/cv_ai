from fastapi import FastAPI
from app.api.routes import router

# Initialize the barebones app with professional metadata
app = FastAPI(
    title="AI HR Assistant API",
    description="Production-ready backend for parsing, scoring, and querying CVs using Groq and local FAISS embeddings.",
    version="1.0.0"
)

# Plug in all the endpoints from our routes.py file
app.include_router(router)

# Run the server on your preferred dev port
if __name__ == "__main__":
    import uvicorn
    # Note: we use "main:app" as a string so the reload flag works properly
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)