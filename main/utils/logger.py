"""
System log utils.
"""
import os
import json
from functools import wraps
from datetime import datetime
from dotenv import load_dotenv
from django.core.handlers.wsgi import WSGIRequest

load_dotenv()
log_folder_path = os.environ.get('LOGS_FOLDER_PATH')


def ensure_log_folder_exists():
    """Ensure that the logs folder exists."""
    if not os.path.exists(log_folder_path):
        os.makedirs(log_folder_path)


def generate_log_content(log_level, func, args, message=None):
    """
    Generate the log content.

    :param log_level: The log level e.g., "INFO", "ERROR", etc.
    :param func: The function that triggers the log.
    :param args: Arguments for the function that triggers the log.
    :param message: Additional log message.
    :return: Formatted log string.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    module_name = func.__module__.split('.')[-3] if func else "Unknown"
    actor_name = func.__module__.split('.')[-1] if func else "Unknown"
    function_name = func.__name__ if func else "Unknown"

    request = args[0] if args else None
    payload = 'Not a Django WSGI Request'

    if isinstance(request, WSGIRequest):
        try:
            payload = json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError:
            payload = 'Invalid JSON or empty payload'

    log_tail = f"payload: {payload}" if message is None else f"message: {message}"

    return f"[{log_level}] time: {timestamp}, module: {module_name}, actor: {actor_name}, function: {function_name}, {log_tail}\n"


def log_trigger(log_level: str):
    """
    Decorator to write logs before calling the api function.

    :param log_level: The log level e.g., "INFO", "ERROR", etc.
    :return: decorator function.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            ensure_log_folder_exists()
            log_file_name = f"{datetime.now().strftime('%Y-%m-%d')}_log.txt"
            log_file_path = os.path.join(log_folder_path, log_file_name)

            log_content = generate_log_content(log_level, func, args)

            with open(log_file_path, "a", encoding="utf8") as file:
                file.write(log_content)

            return func(*args, **kwargs)

        return wrapper

    return decorator


def log_writer(log_level: str, func=None, args=None, message=None):
    """
    Write logs. It can be used during the execution of api function or at the end of execution.

    :param log_level: The log level e.g., "INFO", "ERROR", etc.
    :param func: The function that triggers the log.
    :param args: Arguments for the function that triggers the log..
    :param message: Additional log message.
    """
    ensure_log_folder_exists()
    log_file_name = f"{datetime.now().strftime('%Y-%m-%d')}_log.txt"
    log_file_path = os.path.join(log_folder_path, log_file_name)

    log_content = generate_log_content(log_level, func, args, message)
    print(func.__name__)

    with open(log_file_path, "a", encoding="utf8") as file:
        file.write(log_content)