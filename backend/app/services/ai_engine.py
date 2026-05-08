import os
import logging
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq

# --- MICROSERVICE IMPORTS ---
from app.core.config import INDEX_PATH
from app.schemas.schemas import CandidateAnalysis 

logging.basicConfig(level=logging.INFO)

# --- INITIALIZE MODELS ---
# Using local HuggingFace for robust embeddings and Groq for blazing-fast LLM inference
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
llm = ChatGroq(
    model_name="llama-3.1-8b-instant", 
    temperature=0.2,
    max_retries=2
)

async def process_single_resume_with_llm(file_path: str, jd: str) -> CandidateAnalysis:
    """Extracts text from a PDF and evaluates it against the JD using Groq."""
    try:
        # Isolate PDF loading to catch corrupted files without crashing
        try:
            loader = PyPDFLoader(file_path)
            docs = loader.load()
            resume_text = "\n".join([doc.page_content for doc in docs])
        except Exception as pdf_error:
            raise ValueError(f"Failed to read PDF: {str(pdf_error)}")
        
        prompt = PromptTemplate.from_template(
            """You are a strict, highly analytical Senior Technical Recruiter. 
            Your job is to evaluate a candidate's resume against a specific Job Description (JD).
            
            Job Description:
            {jd}
            
            Candidate Resume:
            {resume_text}
            
            INSTRUCTIONS:
            1. Extract the candidate's full name.
            2. Calculate an ATS Match Score (0-100) based purely on semantic overlap of hard skills, experience years, and required tech stack. Be objective.
            3. List 3 to 5 'strengths' where the candidate aligns perfectly with the JD.
            4. List 1 to 3 'red_flags' (missing skills, lack of required experience, or vague metrics).
            5. Generate 3 highly specific technical interview questions designed to test the candidate on the skills required by the JD that they claim to have.
            
            Return the output strictly in the requested JSON schema."""
        )
        
        structured_llm = llm.with_structured_output(CandidateAnalysis)
        chain = prompt | structured_llm
        
        result = await chain.ainvoke({"jd": jd, "resume_text": resume_text})
        
        if not result:
            raise ValueError("LLM returned empty structured output.")
            
        return result

    except Exception as e:
        logging.error(f"Error processing {file_path}: {e}")
        # Graceful degradation for the UI
        return CandidateAnalysis(
            candidate_name=os.path.basename(file_path),
            ats_match_score=0,
            strengths=[],
            red_flags=[f"System Error during analysis: {str(e)}"],
            interview_questions=[]
        )


async def initialize_rag_vectorstore(directory_path: str):
    """Chunks all uploaded PDFs and creates a persistent FAISS vector database."""
    documents = []
    
    # --- ZONE 1: File Loading (Granular Try-Except per file) ---
    for filename in os.listdir(directory_path):
        if filename.endswith(".pdf"):
            file_path = os.path.join(directory_path, filename)
            try:
                loader = PyPDFLoader(file_path)
                docs = loader.load()
                for doc in docs:
                    doc.metadata["candidate"] = filename
                documents.extend(docs)
            except Exception as pdf_error:
                logging.warning(f"Skipping unreadable PDF {filename}: {str(pdf_error)}")

    if not documents:
        logging.info("No valid text extracted from PDFs. Skipping RAG index creation.")
        return

    # --- ZONE 2: Text Splitting & Embedding ---
    try:
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        chunks = text_splitter.split_documents(documents)
        
        # Generates embeddings using the local HuggingFace model
        vector_store = FAISS.from_documents(chunks, embeddings)
    except Exception as api_error:
        logging.error(f"Embedding generation failed: {str(api_error)}")
        return 

    # --- ZONE 3: Disk I/O (Saving the FAISS index) ---
    try:
        vector_store.save_local(INDEX_PATH)
        logging.info(f"Successfully built and saved FAISS index with {len(chunks)} chunks.")
    except Exception as io_error:
        logging.error(f"Failed to save FAISS index to disk at {INDEX_PATH}: {str(io_error)}")


async def query_rag_system(query: str) -> str:
    """Queries the local FAISS index to answer specific questions about the candidate pool."""
    try:
        # Robust check to ensure the index files actually exist
        faiss_file = os.path.join(INDEX_PATH, "index.faiss")
        pkl_file = os.path.join(INDEX_PATH, "index.pkl")
        
        if not (os.path.exists(faiss_file) and os.path.exists(pkl_file)):
            return "No index found. Please upload resumes first."
            
        # Load from disk
        vector_store = FAISS.load_local(INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
        retriever = vector_store.as_retriever(search_kwargs={"k": 3})
        docs = await retriever.ainvoke(query)
        
        context = "\n\n".join([f"Source: {d.metadata.get('candidate', 'Unknown Document')}\nContent: {d.page_content}" for d in docs])
        
        prompt = PromptTemplate.from_template(
            "Answer the HR query using the context. If unsure, say you don't know.\n"
            "Context: {context}\nQuery: {query}"
        )
        
        chain = prompt | llm
        response = await chain.ainvoke({"context": context, "query": query})
        return response.content
        
    except Exception as e:
        return f"Error querying RAG: {str(e)}"