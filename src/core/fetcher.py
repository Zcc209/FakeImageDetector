# src/core/fetcher.py
import requests
from urllib.parse import urlparse
from src.core.errors import AppError, ErrorCode

# --- 安全限制設定 ---
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 限制最大 10 MB
ALLOWED_CONTENT_TYPES = {'image/jpeg', 'image/png', 'image/webp', 'image/jpg'}
TIMEOUT_SECONDS = 10  # 下載最長等待時間

def is_valid_url(url: str) -> bool:
    """基本網址格式驗證"""
    try:
        result = urlparse(url)
        return all([result.scheme in ['http', 'https'], result.netloc])
    except ValueError:
        return False

def fetch_image_from_url(url: str) -> bytes:
    """
    從 URL 下載圖片並回傳二進位資料 (bytes)。
    具備檔案大小與 MIME type 的雙重安全防護。
    """
    if not is_valid_url(url):
        raise AppError(ErrorCode.INVALID_INPUT, "無效的 URL 格式")

    try:
        # 使用 stream=True 避免一次性將超大檔案載入記憶體
        response = requests.get(url, stream=True, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()

        # 1. 檢查 Content-Type (必須是圖片)
        content_type = response.headers.get('Content-Type', '').lower()
        if content_type not in ALLOWED_CONTENT_TYPES:
            raise AppError(ErrorCode.INVALID_INPUT, f"不支援的檔案類型: {content_type}")

        # 2. 檢查表頭的 Content-Length (初步防禦)
        content_length = response.headers.get('Content-Length')
        if content_length and int(content_length) > MAX_FILE_SIZE_BYTES:
            raise AppError(ErrorCode.INVALID_INPUT, f"圖片檔案過大 (標示為 {int(content_length)/1024/1024:.2f} MB，超過限制 10 MB)")

        # 3. 實際下載並分塊檢查大小 (防止惡意造假 Content-Length)
        image_data = bytearray()
        for chunk in response.iter_content(chunk_size=8192):
            image_data.extend(chunk)
            if len(image_data) > MAX_FILE_SIZE_BYTES:
                raise AppError(ErrorCode.INVALID_INPUT, "下載過程中發現檔案過大，已強制中斷")

        return bytes(image_data)

    except requests.exceptions.Timeout:
        raise AppError(ErrorCode.TIMEOUT_ERROR, f"圖片下載超時 (超過 {TIMEOUT_SECONDS} 秒)")
    except requests.exceptions.RequestException as e:
        raise AppError(ErrorCode.INVALID_INPUT, f"圖片下載失敗: {str(e)}")