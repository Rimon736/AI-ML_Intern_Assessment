import os
import logging
from dotenv import load_dotenv

load_dotenv()

# API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# File Paths
PDF_PATH = "SLATEFALL_DOSSIER.pdf"
DB_PATH = "knowledge_base.sqlite"
OUTPUT_DIR = "outputs"

# LLM Config
QUESTIONS_PER_SECTION = 5

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is not set in the .env file. Please add it to run the LLM.")


# Configure Structured Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("AdaptivePrepSystem")