import os
import shutil
import uuid

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List


from app.core.config import MAX_FILES, MAX_FILE_SIZE_MB, MAX_FILE_SIZE_BYTES, TEMP_DIR
from app.schemas.schemas import BatchAnalysisResponse, ChatRequest, ChatResponse
from app.services import ai_engine

router = APIRouter()

@router.post("/analyze_batch", response_model=BatchAnalysisResponse)
async def analyze_batch(job_description: str = Form(...), files: List[UploadFile] = File(...)):
    
    # --- STEP 1: VALIDATE FIRST (No destructive actions yet) ---
    if len(files) > MAX_FILES:
        raise HTTPException(status_code=400, detail=f"Maximum {MAX_FILES} resumes allowed per batch.")

    for file in files:
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail=f"File {file.filename} is not a PDF.")
            
        file.file.seek(0, os.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)
        
        if file_size > MAX_FILE_SIZE_BYTES:
            raise HTTPException(status_code=400, detail=f"File {file.filename} exceeds {MAX_FILE_SIZE_MB}MB limit.")

               
   
    
    # Clear old FAISS index so the new batch doesn't mix with old candidates
    if os.path.exists(ai_engine.INDEX_PATH):
        shutil.rmtree(ai_engine.INDEX_PATH)

    # -- PROCESS NEW BATCH --
    saved_paths = []
    for file in files:
        unique_filename = f"{uuid.uuid4().hex[:8]}_{file.filename}"
        path = os.path.join(TEMP_DIR, unique_filename) 
        
        with open(path, "wb") as buffer:            
            shutil.copyfileobj(file.file, buffer)
        saved_paths.append(path)
    try:
        results = []
        for path in saved_paths:
            analysis = await ai_engine.process_single_resume_with_llm(path, job_description)
            results.append(analysis)

        await ai_engine.initialize_rag_vectorstore(TEMP_DIR)
        return BatchAnalysisResponse(job_description=job_description, results=results)
    finally:
        for path in saved_paths:
            if os.path.exists(path):
                os.remove(path)

@router.post("/chat_cv", response_model=ChatResponse)
async def chat(request: ChatRequest):
    answer = await ai_engine.query_rag_system(request.query)
    return ChatResponse(answer=answer)
