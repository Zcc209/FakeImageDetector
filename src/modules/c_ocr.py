import numpy as np
from core.registry import register_module

@register_module("ocr")
def run_ocr(img_array: np.ndarray, config: dict) -> dict:
    """ PaddleOCR 文字萃取模組 """
    print("  [Module] OCR 執行中...")
    return {
        "ocr_text": "發現高風險文字"
    }