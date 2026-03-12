# src/core/quality_gate.py
import cv2
import numpy as np

def check_image_quality(img_array: np.ndarray, config: dict = None) -> dict:
    """
    畫質 Gate v1：檢測模糊、低光、解析度過低。
    攔截無效圖片，節省後續 AI 模型的算力。
    """
    if config is None:
        config = {}
        
    # 讀取門檻值設定，若無則使用預設值
    thresholds = config.get("quality_gate", {
        "min_width": 150,
        "min_height": 150,
        "min_blur_score": 100.0, # Laplacian 變異數 (越低越模糊)
        "min_brightness": 30.0,  # 灰階平均值 (越低越暗)
        "max_brightness": 240.0  # 灰階平均值 (越高越曝)
    })

    h, w = img_array.shape[:2]
    
    # 將 RGB 轉為灰階影像以計算 CV 指標
    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_array

    reasons = []
    metrics = {}

    # 1. 解析度過低 (Low Resolution)
    metrics["resolution"] = [w, h]
    if w < thresholds["min_width"] or h < thresholds["min_height"]:
        reasons.append("low_resolution")

    # 2. 模糊檢測 (Blur Detection)
    # 使用拉普拉斯算子 (Laplacian) 計算變異數。邊緣越豐富數值越高，越模糊數值越趨近 0。
    blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
    metrics["blur_score"] = round(blur_score, 2)
    if blur_score < thresholds["min_blur_score"]:
        reasons.append("too_blurry")

    # 3. 亮度檢測 (Light / Exposure)
    # 計算整張圖片的平均灰階值 (0=全黑, 255=全白)
    brightness = np.mean(gray)
    metrics["brightness"] = round(brightness, 2)
    if brightness < thresholds["min_brightness"]:
        reasons.append("too_dark")
    elif brightness > thresholds["max_brightness"]:
        reasons.append("too_bright")

    # (備註) 壓縮嚴重 (Heavy Compression)
    # 傳統 CV 抓壓縮失真較耗時，V1 實務上解析度與模糊度檢查已能擋下 90% 的嚴重壓縮圖。
    # 留待後續依據實測需要再加入 JPEG 區塊雜訊 (Blockiness) 檢測。

    # 綜合判斷：如果 reasons 是空的，代表圖夠清晰，放行！
    is_valid = len(reasons) == 0

    return {
        "is_valid": is_valid,
        "reasons": reasons,
        "metrics": metrics
    }