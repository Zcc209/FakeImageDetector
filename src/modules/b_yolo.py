import numpy as np
from core.registry import register_module

# B 組注意：請務必使用同一個函式簽名 run(img_array, config) -> dict
@register_module("yolo")
def run_yolo(img_array: np.ndarray, config: dict) -> dict:
    """ YOLOv8 物件偵測模組 """
    # TODO: B組在這裡寫模型推論程式碼
    # 以下為暫時的測試假資料 (Stub)
    
    print("  [Module] YOLO 執行中...")
    return {
        "yolo_objects": [{"label": "person", "confidence": 0.95, "box": [0,0,10,10]}],
        "is_tampered": False
    }