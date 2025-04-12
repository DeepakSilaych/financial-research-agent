import logging
import os
from datetime import datetime
from typing import Optional

# Define log levels
INFO = logging.INFO
DEBUG = logging.DEBUG
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL

# Create logs directory if it doesn't exist
logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
os.makedirs(logs_dir, exist_ok=True)

# Generate log filename with current date
current_date = datetime.now().strftime("%Y-%m-%d")
log_file = os.path.join(logs_dir, f"app_{current_date}.log")

# Configure the logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()  # Also output to console
    ]
)

def get_logger(name: Optional[str] = None):
    """
    Get a logger instance with the given name.
    
    Args:
        name: The name for the logger. If None, returns the root logger.
        
    Returns:
        A configured logger instance
    """
    return logging.getLogger(name)

# Create default application logger
app_logger = get_logger("finance_app")

def info(message: str, logger=None):
    """Log an info message"""
    (logger or app_logger).info(message)

def debug(message: str, logger=None):
    """Log a debug message"""
    (logger or app_logger).debug(message)

def warning(message: str, logger=None):
    """Log a warning message"""
    (logger or app_logger).warning(message)

def error(message: str, logger=None):
    """Log an error message"""
    (logger or app_logger).error(message)

def critical(message: str, logger=None):
    """Log a critical message"""
    (logger or app_logger).critical(message)

def log_tool_call(tool_name: str, input_data: str, output_data: str = None, error: str = None):
    """
    Log a tool call with input and output data
    
    Args:
        tool_name: Name of the tool being called
        input_data: Input data sent to the tool
        output_data: Output data received from the tool (optional)
        error: Error message if the tool call failed (optional)
    """
    if error:
        app_logger.error(f"TOOL CALL: {tool_name} - INPUT: {input_data} - ERROR: {error}")
    elif output_data:
        # For large outputs, truncate to avoid massive log files
        if len(output_data) > 1000:
            output_preview = output_data[:1000] + "... [truncated]"
        else:
            output_preview = output_data
        app_logger.info(f"TOOL CALL: {tool_name} - INPUT: {input_data} - OUTPUT: {output_preview}")
    else:
        app_logger.info(f"TOOL CALL: {tool_name} - INPUT: {input_data}")

def log_request(user_id: str, query: str, metadata: dict = None):
    """
    Log a user request
    
    Args:
        user_id: User identifier
        query: The user's query text
        metadata: Additional metadata about the query (optional)
    """
    metadata_str = str(metadata) if metadata else ""
    app_logger.info(f"REQUEST: User={user_id} - Query='{query}' - Metadata={metadata_str}")

def log_response(user_id: str, query: str, response: str):
    """
    Log a response sent to the user
    
    Args:
        user_id: User identifier
        query: The original query
        response: The response text
    """
    # Truncate long responses in logs
    if len(response) > 1000:
        response_preview = response[:1000] + "... [truncated]"
    else:
        response_preview = response
    
    app_logger.info(f"RESPONSE: User={user_id} - Query='{query}' - Response='{response_preview}'")

# Example usage
if __name__ == "__main__":
    info("This is an info message")
    debug("This is a debug message")
    warning("This is a warning message")
    error("This is an error message")
    critical("This is a critical message")
    
    log_tool_call("StockInfo", "AAPL", "Apple Inc. (AAPL) - Price: $173.82")
    log_request("user123", "What is the current price of TSLA?")
    log_response("user123", "What is the current price of TSLA?", "Tesla Inc. (TSLA) - Price: $177.90") 