# src/core/utils.py
import functools
import traceback
import concurrent.futures
from .errors import ErrorCode, AppError, build_error_response

def safe_run(timeout_seconds: int = 10):
    """
    安全執行裝飾器：
    1. 捕捉所有未預期的 Exception。
    2. 實作 Timeout 超時強制中斷機制。
    3. 將錯誤轉換為標準 JSON 格式回傳。
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 定義實際要執行的任務
            def task():
                return func(*args, **kwargs)

            try:
                # 使用 ThreadPoolExecutor 來實作 Timeout
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(task)
                    # 等待結果，若超過 timeout_seconds 則拋出 TimeoutError
                    result = future.result(timeout=timeout_seconds)
                    return result
                    
            except concurrent.futures.TimeoutError:
                msg = f"Module '{func.__name__}' execution timed out after {timeout_seconds}s."
                print(f"[ERROR] {msg}")
                return build_error_response(ErrorCode.TIMEOUT_ERROR, msg)
                
            except AppError as e:
                # 捕捉我們自己定義的已知錯誤
                print(f"[ERROR] AppError in '{func.__name__}': {e.message}")
                return build_error_response(e.code, e.message)
                
            except Exception as e:
                # 捕捉所有未知的 Crash (例如 OOM、除以零、型別錯誤)
                error_trace = traceback.format_exc()
                msg = f"Unexpected error in '{func.__name__}': {str(e)}"
                print(f"[FATAL] {msg}\n{error_trace}")
                return build_error_response(ErrorCode.UNKNOWN_ERROR, msg)
                
        return wrapper
    return decorator