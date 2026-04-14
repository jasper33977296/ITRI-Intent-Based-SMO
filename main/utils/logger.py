"""
System log utils.
"""
import os
import json
import traceback
from functools import wraps
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from asgiref.sync import sync_to_async

_TZ_TAIPEI = timezone(timedelta(hours=8))

load_dotenv()
log_folder_path = os.environ.get('LOGS_FOLDER_PATH')


def ensure_log_folder_exists():
    """Ensure that the logs folder exists."""
    if not os.path.exists(log_folder_path):
        os.makedirs(log_folder_path)

def generate_log_content(log_level, status_code, source_type='system', func=None, args=None, message=None):
    """
    根據來源（內部模組、外部系統）產生對應格式的 log 字串
    - source_type: 'system' | 'dify engine'
    """
    timestamp = datetime.now(_TZ_TAIPEI).strftime("%Y-%m-%d %H:%M:%S")

    if isinstance(func, str):
        log_str = f"[{log_level}] [{status_code}] [{source_type}]: {func} [message]: {message}"
    else:
        module = func.__module__.split('.')[-3] if func else "Unknown"
        actor = func.__module__.split('.')[-1] if func else "Unknown"
        func_name = func.__name__ if func else "Unknown"

        log_str = f"[{log_level}] [{status_code}] [{source_type}]: {module}/ {actor}/ {func_name} [message]: {message}"

    return f"{timestamp} - {log_str}\n" 


def log_trigger():
    """
    decorator：記錄執行成功與例外錯誤的 log
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            ensure_log_folder_exists()
            log_file_name = f"{datetime.now(_TZ_TAIPEI).strftime('%Y-%m-%d')}_log.txt"
            log_file_path = os.path.join(log_folder_path, log_file_name)

            try:
                result = func(*args, **kwargs)

                # 解析回傳的 JsonResponse 內容
                try:
                    if hasattr(result, "content"):
                        content = json.loads(result.content.decode("utf-8"))
                        status_code = (
                            str(content["status_code"]) if "status_code" in content else "600"
                        )
                        message = content.get("message", "No message")
                    else:
                        status_code = "601"
                        message = "Successfully"
                except Exception:
                    status_code = "801"
                    message = "Exception"

                log_content = generate_log_content(
                    log_level="INFO",
                    status_code=status_code,
                    func=func,
                    args=args,
                    message=message
                )
                with open(log_file_path, "a", encoding="utf8") as f:
                    f.write(log_content)
                return result

            except Exception as e:
                # 捕捉錯誤，記錄錯誤 log
                error_type = type(e).__name__
                error_trace = traceback.format_exc()
                log_content = generate_log_content(
                    log_level="ERROR",
                    status_code="801",
                    func=func,
                    args=args,
                    message=f"[{error_type}]: {str(e)} [{{error_trace}}]: {error_trace}"
                )
                with open(log_file_path, "a", encoding="utf8") as f:
                    f.write(log_content)

        return wrapper
    return decorator


def log_writer(log_level, status_code, source_type='system', func=None, args=None, message=None):
    """
    提供給非 decorator 的 log 記錄方式（手動調用）
    - log_level: INFO, ERROR 等
    - status_code: 狀態碼
    - source_type: 'system' | 'dify engine'
    """
    ensure_log_folder_exists()
    log_file_name = f"{datetime.now(_TZ_TAIPEI).strftime('%Y-%m-%d')}_log.txt"
    log_file_path = os.path.join(log_folder_path, log_file_name)

    log_content = generate_log_content(log_level, status_code, source_type, func, args, message)

    with open(log_file_path, "a", encoding="utf8") as file:
        file.write(log_content)

@sync_to_async
def async_log_writer(*args, **kwargs):
    log_writer(*args, **kwargs)
