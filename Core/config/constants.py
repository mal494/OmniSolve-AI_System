"""
Constants and configuration values for OmniSolve.
All hardcoded values should be defined here for easy management.
"""
import logging
import os

# --- API CONFIGURATION ---
API_URL = os.getenv("OMNISOLVE_API_URL", "http://localhost:5001/api/v1/generate")
API_TIMEOUT = int(os.getenv("OMNISOLVE_API_TIMEOUT", "120"))  # seconds

# --- BRAIN BACKEND ---
# Supported: kobold, openai, anthropic, mock
BRAIN_BACKEND = os.getenv("OMNISOLVE_BRAIN_BACKEND", "kobold")

# --- GENERATION PARAMETERS ---
DEFAULT_MAX_CONTEXT_LENGTH = 8192
DEFAULT_MAX_LENGTH = 2048
DEFAULT_TEMPERATURE = 0.3
RETRY_TEMPERATURE_INCREMENT = 0.1  # Increase temp on retry

# --- RETRY LOGIC ---
MAX_RETRIES = int(os.getenv("OMNISOLVE_MAX_RETRIES", "3"))
RETRY_DELAY = float(os.getenv("OMNISOLVE_RETRY_DELAY", "1.0"))  # base seconds (exponential backoff)
RETRY_DELAY_MAX = float(os.getenv("OMNISOLVE_RETRY_DELAY_MAX", "30.0"))  # cap for backoff

# --- CIRCUIT BREAKER ---
CIRCUIT_BREAKER_THRESHOLD = int(os.getenv("OMNISOLVE_CB_THRESHOLD", "5"))  # failures before opening
CIRCUIT_BREAKER_TIMEOUT = float(os.getenv("OMNISOLVE_CB_TIMEOUT", "60.0"))  # seconds before half-open

# --- PARALLEL FILE GENERATION ---
PARALLEL_FILE_GENERATION = os.getenv("OMNISOLVE_PARALLEL", "false").lower() == "true"

# --- PATHS ---
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROJECTS_DIR = os.path.join(ROOT_DIR, "Projects")
CONFIG_DIR = os.path.join(ROOT_DIR, "Config")
LOGS_DIR = os.path.join(ROOT_DIR, "Logs")
SESSIONS_DIR = os.path.join(LOGS_DIR, "sessions")
GENERATED_SOFTWARE_DIR = os.path.join(ROOT_DIR, "Generated_Software")

# --- STOP TOKENS ---
STOP_TOKENS = [
    "SYSTEM ROLE:",
    "[CURRENT TASK]",
    "[END]",
    "USER:",
    "ASSISTANT:"
]

# --- PSI CONFIGURATION ---
PSI_CACHE_TIMEOUT = 300  # Cache PSI for 5 minutes
PSI_MAX_FILES = 100  # Summarize if project has more files

# --- LOGGING ---
_raw_log_level = os.getenv("OMNISOLVE_LOG_LEVEL", "INFO").upper()
LOG_LEVEL = _raw_log_level if hasattr(logging, _raw_log_level) else "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
ENABLE_AUDIT_LOG = os.getenv("OMNISOLVE_AUDIT_LOG", "true").lower() == "true"

# --- PERSONA FILES ---
PERSONA_MAPPING = {
    "Architect": "Architect.json",
    "Planner": "Planner.json",
    "Developer": "Developer.json",  # Note: actually loads Steve.json
    "QA": "QA.json"
}
