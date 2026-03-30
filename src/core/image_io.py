import os
import requests
import cv2
import numpy as np
from .errors import AppError, ErrorCode
from io import BytesIO
from PIL import Image, UnidentifiedImageError

class ImageLoadError(Exception):
    """自定義的圖片讀取錯誤，方便上層系統捕捉"""
    pass

def load_image(source: str) -> Image.Image:
    """
    統一讀取圖片的入口函數。
    根據輸入字串自動判斷是 URL 還是本地路徑。
    """
    if source.startswith("http://") or source.startswith("https://"):
        return _download_image(source)
    else:
        return _load_local_image(source)

def _download_image(url: str, timeout: int = 10) -> Image.Image:
    """從 URL 下載圖片並轉換為 PIL Image"""
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status() 
        img = Image.open(BytesIO(response.content))
        img.load() 
        return img
    except requests.exceptions.RequestException as e:
        raise ImageLoadError(f"網路圖片下載失敗: {e}")
    except UnidentifiedImageError:
        raise ImageLoadError(f"無法辨識的圖片格式: {url}")
    except Exception as e:
        raise ImageLoadError(f"未期的錯誤: {e}")

def _load_local_image(path: str) -> Image.Image:
    """從本地端讀取圖片並轉換為 PIL Image"""
    if not os.path.exists(path):
        raise ImageLoadError(f"找不到檔案: {path}")
    try:
        img = Image.open(path)
        img.load() 
        return img
    except UnidentifiedImageError:
        raise ImageLoadError(f"無法辨識的圖片格式: {path}")
    except Exception as e:
        raise ImageLoadError(f"未期的錯誤: {e}")

def load_image_from_bytes(image_bytes: bytes) -> np.ndarray:
    """
    將網路抓下來的二進位圖片資料 (bytes) 轉換為 numpy array。
    預設轉換為 OpenCV 標準的 BGR 格式。
    """
    try:
        # 1. 將 bytes 轉成一維 numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        
        # 2. 解碼成 OpenCV 圖片矩陣 (如果解碼失敗會回傳 None)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            # 觸發我們 W7 寫好的統一錯誤處理
            raise AppError(ErrorCode.INVALID_INPUT, "無法解碼圖片資料，檔案可能已損毀或格式不支援")
            
        return img
        
    except AppError:
        raise
    except Exception as e:
        raise AppError(ErrorCode.INVALID_INPUT, f"讀取圖片 bytes 發生未預期錯誤: {str(e)}")