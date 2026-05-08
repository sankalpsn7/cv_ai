# 🧠 Applied AI CV Analyzer & RAG Pipeline

> A resilient, backend-focused AI pipeline designed to evaluate candidate CVs against Job Descriptions using a hybrid architecture of local HuggingFace embeddings and Groq's blazing-fast LPU inference.

## 🏗️ System Architecture

This project was engineered to demonstrate **scalable backend architecture, fault tolerance, and applied AI integration**. By decoupling the embedding generation from the cloud LLM, the system achieves zero-latency vectorization while completely bypassing third-party rate limits (429 errors).

### **Core Architectural Decisions**
* **Hybrid AI Pipeline:** Leverages **HuggingFace (`all-MiniLM-L6-v2`)** running locally on CPU for chunking and embedding, while offloading heavy semantic reasoning to **Groq (Llama 3)** for structured JSON extraction.
* **Stateless Vector Persistence:** Uses **FAISS** to generate temporary, per-batch vector indexes directly to disk. This prevents in-memory collisions across concurrent API requests and ensures a stateless backend environment.
* **Microservice Backend:** A **FastAPI** application designed with strict separation of concerns—isolating Routers, AI Services, Data Validation (Pydantic Schemas), and Core Configurations.
* **Graceful Degradation:** Granular `try/except` handling at the ingestion, embedding, and inference layers ensures that a single corrupted PDF does not crash the entire batch pipeline.
* **Lightweight Client:** A minimal **Streamlit** interface acts solely as a REST API consumer to interact with the backend endpoints.

---

## 🔄 Data Workflow

### 1. Ingestion & Evaluation Flow (Batch Processing)
```text

# 🧠 Applied AI CV Analyzer & RAG Pipeline

> A resilient, backend-focused AI pipeline designed to evaluate candidate CVs against Job Descriptions using a hybrid architecture of local HuggingFace embeddings and Groq's blazing-fast LPU inference.

---

## 🏗️ System Architecture

This project demonstrates **scalable backend architecture, fault tolerance, and applied AI integration**. By decoupling embedding generation from the cloud LLM, the system achieves zero-latency vectorization and bypasses third-party rate limits (429 errors).

### Core Architectural Decisions

- **Hybrid AI Pipeline:**
  - Local: HuggingFace (`all-MiniLM-L6-v2`) for chunking and embedding (CPU)
  - Cloud: Groq (Llama 3) for structured JSON extraction
- **Stateless Vector Persistence:**
  - FAISS generates per-batch vector indexes to disk, preventing in-memory collisions and ensuring statelessness
- **Microservice Backend:**
  - FastAPI app with strict separation of Routers, AI Services, Pydantic Schemas, and Core Configurations
- **Graceful Degradation:**
  - Granular `try/except` handling at ingestion, embedding, and inference layers (one bad PDF won't crash the batch)
- **Lightweight Client:**
  - Minimal Streamlit UI acts as a REST API consumer

---

## 🔄 Data Workflow

### 1. Ingestion & Evaluation Flow (Batch Processing)

```mermaid
flowchart TD
    A([PDF Uploads] + [Job Description]) -->|FastAPI /analyze_batch| B[Validation Layer]
    B -- Rejects non-PDFs/oversized files --> B
    B -->|PyPDFLoader| C[Text Extraction]
    C -->|Groq API (Llama 3)| D[Evaluate CV vs JD]
    D -->|JSON Payload| E[(ATS Score, Strengths, Red Flags, QA)]
    C -->|Text Splitter| F[HuggingFace Local Embeddings]
    F -->|FAISS| G[Saved locally (/faiss_index) for RAG]
```

### 2. RAG Flow

```mermaid
flowchart TD
    H["User HR Query:<br/>Which candidate has experience with PostgreSQL?"]
        -->|FastAPI /chat_cv| I["Local FAISS Index"]

    I -->|Semantic Search| J["Top-K CV Chunks"]

    J -->|Prompt Engineering| K["Context + Query"]

    K -->|Groq API (Llama 3)| L["Targeted Answer"]
```

---

## 🛠️ Tech Stack

| Layer              | Technology                                             |
|--------------------|--------------------------------------------------------|
| AI & NLP           | LangChain, Groq API (Llama-3.1-8b), HuggingFace        |
| Backend Framework  | FastAPI, Python, Uvicorn, Pydantic                     |
| Vector Database    | FAISS (Local CPU)                                      |
| Frontend Consumer  | Streamlit, Requests, Pandas                            |

---

## 🚀 Getting Started (Local Development)

### 1. Clone the repository and set up your environment

Ensure you have Python installed. You will need a free API key from Groq.

Create a `.env` file in the root directory:

```env
GROQ_API_KEY=your_api_key_here
```

---

### 2. Start the Backend Server

Open your first terminal and navigate to the backend directory:

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 5000 --reload
```

> **Note:** The backend runs on port 5000 by default. The first run will take ~15 seconds to download the local HuggingFace embedding model.

---

### 3. Start the Frontend UI

Open a second terminal and navigate to the frontend directory:

```bash
cd frontend
pip install -r requirements.txt
streamlit run app.py
```

The application will automatically launch in your browser at [http://localhost:8501](http://localhost:8501)