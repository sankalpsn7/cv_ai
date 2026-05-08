import os
from dotenv import load_dotenv

# Load environment variables (like your GROQ_API_KEY)
load_dotenv()

# --- GLOBAL APP SETTINGS ---
TEMP_DIR = "temp_resumes"
INDEX_PATH = "faiss_index"

MAX_FILES = 5
MAX_FILE_SIZE_MB = 5
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# Ensure the temp directory exists as soon as the app starts
os.makedirs(TEMP_DIR, exist_ok=True)