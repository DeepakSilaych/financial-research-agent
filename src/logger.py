import logging
import os
from datetime import datetime
from typing import Optional, Any
import json

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

def info(message: str) -> None:
    """Log an info message."""
    app_logger.info(message)

def warning(message: str) -> None:
    """Log a warning message."""
    app_logger.warning(message)

def error(message: str, exc_info: bool = False) -> None:
    """
    Log an error message.
    
    Args:
        message: The error message to log
        exc_info: Whether to include exception info in the log
    """
    app_logger.error(message, exc_info=exc_info)

def log_tool_call(tool_name: str, input_data: Any, output_data: Any, metadata: dict = None) -> None:
    """
    Log a tool call with input and output data.
    
    Args:
        tool_name: The name of the tool being called
        input_data: The input to the tool
        output_data: The output from the tool
        metadata: Additional metadata about the tool call
    """
    if metadata is None:
        metadata = {}
    
    input_str = str(input_data)
    output_str = str(output_data)
    
    # Truncate long inputs/outputs for better log readability
    truncated_input = input_str[:1000] + "..." if len(input_str) > 1000 else input_str
    truncated_output = output_str[:1000] + "..." if len(output_str) > 1000 else output_str
    
    # Format a readable timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    
    # Log the tool call summary
    app_logger.info(f"[{timestamp}] Tool call: {tool_name}")
    app_logger.info(f"Tool input (truncated): {truncated_input}")
    app_logger.info(f"Tool output (truncated): {truncated_output}")
    
    # Log additional metadata if available
    if metadata:
        app_logger.info(f"Tool metadata: {json.dumps(metadata, indent=2)}")
    
    # Store detailed information in the log file
    input_output_log = {
        "timestamp": timestamp,
        "tool_name": tool_name,
        "input": input_data,
        "output": output_data,
        "metadata": metadata
    }
    
    # Write to the detailed log file
    try:
        with open(os.path.join(logs_dir, "tool_calls.jsonl"), "a") as f:
            f.write(json.dumps(input_output_log) + "\n")
    except Exception as e:
        app_logger.error(f"Failed to write tool call to log file: {str(e)}")

def log_agent_output(agent_name: str, input_text: str, output_text: str, metadata: dict = None) -> None:
    """
    Log an agent's output with input and output data.
    
    Args:
        agent_name: The name of the agent
        input_text: The input to the agent
        output_text: The output from the agent
        metadata: Additional metadata about the agent's operation
    """
    if metadata is None:
        metadata = {}
    
    # Truncate long inputs/outputs for better log readability
    truncated_input = input_text[:500] + "..." if len(input_text) > 500 else input_text
    truncated_output = output_text[:500] + "..." if len(output_text) > 500 else output_text
    
    # Format a readable timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    
    # Log the agent output summary
    app_logger.info(f"[{timestamp}] Agent output: {agent_name}")
    app_logger.info(f"Agent input (truncated): {truncated_input}")
    app_logger.info(f"Agent output (truncated): {truncated_output}")
    
    # Log additional metadata if available
    if metadata:
        metadata_str = json.dumps(metadata, indent=2)
        app_logger.info(f"Agent metadata: {metadata_str}")
    
    # Store detailed information in the log file
    agent_log = {
        "timestamp": timestamp,
        "agent_name": agent_name,
        "input": input_text,
        "output": output_text,
        "metadata": metadata
    }
    
    # Write to the detailed log file
    try:
        with open(os.path.join(logs_dir, "agent_outputs.jsonl"), "a") as f:
            f.write(json.dumps(agent_log) + "\n")
    except Exception as e:
        app_logger.error(f"Failed to write agent output to log file: {str(e)}")
        
        
def debug(message: str, data: Any = None) -> None:
    """
    Log a debug message with optional data dump.
    
    Args:
        message: Debug message to log
        data: Optional data to include in the log
    """
    app_logger.debug(message)
    
    if data is not None:
        if isinstance(data, (dict, list)):
            try:
                formatted_data = json.dumps(data, indent=2)
                app_logger.debug(f"Debug data: {formatted_data}")
            except:
                app_logger.debug(f"Debug data (non-serializable): {str(data)}")
        else:
            app_logger.debug(f"Debug data: {str(data)}")

def log_request(user_id: str, query: str, metadata: dict = None) -> None:
    """
    Log a user request
    
    Args:
        user_id: User identifier
        query: The user's query text
        metadata: Additional metadata about the query (optional)
    """
    if metadata is None:
        metadata = {}
    
    metadata_str = json.dumps(metadata) if metadata else "{}"
    
    # Truncate long queries for console logging
    truncated_query = query[:100] + "..." if len(query) > 100 else query
    
    app_logger.info(f"REQUEST: User={user_id} - Query='{truncated_query}'")
    
    # Store detailed request information
    request_log = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
        "user_id": user_id,
        "query": query,
        "metadata": metadata
    }
    
    # Write to the detailed log file
    try:
        with open(os.path.join(logs_dir, "user_requests.jsonl"), "a") as f:
            f.write(json.dumps(request_log) + "\n")
    except Exception as e:
        app_logger.error(f"Failed to write request to log file: {str(e)}")

def log_response(user_id: str, query_or_response: str, response: str = None) -> None:
    """
    Log a response sent to the user
    
    This function accepts two calling patterns:
    1. log_response(user_id, query, response) - Original pattern
    2. log_response(user_id, response) - New pattern, query is omitted
    
    Args:
        user_id: User identifier
        query_or_response: Either the original query (if response is provided) or the response (if response is None)
        response: The response text (optional - if not provided, query_or_response is treated as the response)
    """
    # Determine if we're using the new or old calling pattern
    if response is None:
        # New pattern: log_response(user_id, response)
        actual_response = query_or_response
        query_str = "(query omitted)"
    else:
        # Original pattern: log_response(user_id, query, response)
        actual_response = response
        query_str = query_or_response
    
    # Truncate long responses in logs
    truncated_response = actual_response[:500] + "..." if len(actual_response) > 500 else actual_response
    truncated_query = query_str[:100] + "..." if len(query_str) > 100 else query_str
    
    app_logger.info(f"RESPONSE: User={user_id} - Query='{truncated_query}' - Response='{truncated_response}'")
    
    # Store detailed response information
    response_log = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
        "user_id": user_id,
        "query": query_str if query_str != "(query omitted)" else None,
        "response": actual_response
    }
    
    # Write to the detailed log file
    try:
        with open(os.path.join(logs_dir, "user_responses.jsonl"), "a") as f:
            f.write(json.dumps(response_log) + "\n")
    except Exception as e:
        app_logger.error(f"Failed to write response to log file: {str(e)}")

# Example usage
if __name__ == "__main__":
    info("This is an info message")
    warning("This is a warning message")
    error("This is an error message")
    
    log_tool_call("StockInfo", "AAPL", "Apple Inc. (AAPL) - Price: $173.82")
    log_agent_output("StockInfo", "AAPL", "Apple Inc. (AAPL) - Price: $173.82") 