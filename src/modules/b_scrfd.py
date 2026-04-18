# src/modules/b_scrfd.py
import cv2
import numpy as np
import onnxruntime as ort
from insightface.app import FaceAnalysis
from core.registry import register_module

# 宣告全域變數來暫存模型，避免批次處理時重複載入浪費時間
_app = None

@register_module("scrfd")
def run_scrfd(img_array: np.ndarray, config: dict) -> dict:
    """ SCRFD 人臉偵測真實模組 """
    global _app
    print("  [Module] SCRFD 真實模型執行中...")
    
    # 1. 系統初次執行時，載入並初始化模型
    if _app is None:
        print("    -> [SCRFD] 系統初次載入模型中 (若無模型會自動下載，請稍候)...")
        # 判斷是否在有 GPU 的環境 (對應 Colab 的 T4 GPU)
        available = ort.get_available_providers()
        if "CUDAExecutionProvider" in available:
            providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
            ctx_id = 0
        else:
            providers = ["CPUExecutionProvider"]
            ctx_id = -1
            
        # 設定模型自動下載的存放目錄 (掛載在你的雲端硬碟以免斷線消失)
        model_root = "/content/drive/MyDrive/FakeImageDetector/models_weights/scrfd"
        
        # 照著 B 同學的參數初始化 buffalo_l 模型
        _app = FaceAnalysis(
            name="buffalo_l",
            root=model_root,
            allowed_modules=["detection"],
            providers=providers
        )
        _app.prepare(ctx_id=ctx_id, det_size=(640, 640))
        print("    -> [SCRFD] 模型準備完畢！")

    # 2. 顏色通道轉換 (A組產線是 RGB，但 Insightface 底層吃 BGR)
    img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

    # 3. 執行推論 (呼叫 B 同學的 app.get 邏輯)
    faces = _app.get(img_bgr)
    
    # 4. 整理臉框
    scrfd_faces = []
    for f in faces:
        x1, y1, x2, y2 = map(int, f.bbox.tolist())
        score = float(getattr(f, "det_score", 0.0))
        scrfd_faces.append({
            "box": [x1, y1, x2, y2],
            "score": round(score, 4)
        })

    return {
        "scrfd_face_count": len(scrfd_faces),
        "scrfd_faces": scrfd_faces
    }