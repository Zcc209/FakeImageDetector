import numpy as np
from core.registry import register_module

@register_module("scrfd")
def run_scrfd(img_array: np.ndarray, config: dict) -> dict:
    """ SCRFD 人臉偵測模組 """
    print("  [Module] SCRFD (人臉偵測) 執行中...")
    return {
        "scrfd_face_count": 1
    }