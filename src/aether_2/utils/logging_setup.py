import os
import csv
import logging
from datetime import datetime

# Setup logging for file-based debugging (minimal console output)
def setup_logging():
    """Setup logging to files only, minimal console output"""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, 'crewai_debug.log')
    formatter = logging.Formatter('%(asctime)s - %(thread)d - %(name)s-%(filename)s:%(funcName)s:%(lineno)d - %(levelname)s: %(message)s')

    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Attach directly to the root logger — works even if basicConfig was already called
    root_logger = logging.getLogger()
    # Avoid adding duplicate handlers on re-import
    if not any(isinstance(h, logging.FileHandler) and getattr(h, 'baseFilename', None) and h.baseFilename.endswith('crewai_debug.log') for h in root_logger.handlers):
        root_logger.addHandler(file_handler)
    root_logger.setLevel(logging.DEBUG)

    # Set specific loggers to DEBUG level for file logging
    for logger_name in ['crewai', 'crewai.agent', 'crewai.task', 'crewai.crew',
                        'openai', 'anthropic', 'google.cloud', 'httpx', 'urllib3']:
        logging.getLogger(logger_name).setLevel(logging.DEBUG)

    # Create a custom logger for our application
    app_logger = logging.getLogger('aether_2')
    app_logger.setLevel(logging.INFO)

    return app_logger

# Setup CSV logging for execution tracking
def setup_csv_logging():
    """Setup CSV logging for execution tracking"""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # Create CSV filename with current date
    today = datetime.now().strftime("%Y-%m-%d")
    csv_file = os.path.join(log_dir, f"execution_log_{today}.csv")
    
    # Create CSV file with headers if it doesn't exist
    if not os.path.exists(csv_file):
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['user_id', 'start_time', 'end_time', 'duration_seconds', 'status'])
    
    return csv_file

# Initialize logging
logger = setup_logging()

# Disable LiteLLM console logging (keep file logging only)
logging.getLogger("LiteLLM").setLevel(logging.WARNING)
logging.getLogger("litellm").setLevel(logging.WARNING)
logging.getLogger("LiteLLM:DEBUG").setLevel(logging.WARNING)
logging.getLogger("LiteLLM:utils").setLevel(logging.WARNING)
logging.getLogger("LiteLLM:vertex_llm_base").setLevel(logging.WARNING)
logging.getLogger("LiteLLM:litellm_logging").setLevel(logging.WARNING)

# Setup CSV logging
csv_log_file = setup_csv_logging()
logger.info(f"📊 CSV execution log: {csv_log_file}")

