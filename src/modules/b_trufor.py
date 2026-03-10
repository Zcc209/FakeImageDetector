# src/modules/b_trufor.py
import os
import subprocess
import numpy as np
from PIL import Image
from core.registry import register_module

@register_module("trufor")
def run_trufor(img_array: np.ndarray, config: dict) -> dict:
    """ TruFor 鑑偽模組 (透過 Subprocess 隔離環境執行) """
    print("  [Module] TruFor 執行中...")
    
    # 1. 將 A 組傳來的 ndarray 轉存為暫存圖 (因為 TruFor 的 test.py 只吃資料夾路徑)
    tmp_in_dir = "temp/trufor_in"
    tmp_out_dir = "temp/trufor_out"
    os.makedirs(tmp_in_dir, exist_ok=True)
    os.makedirs(tmp_out_dir, exist_ok=True)
    
    img_path = os.path.join(tmp_in_dir, "temp_img.jpg")
    Image.fromarray(img_array).save(img_path)
    
    # 2. 組合命令列指令 (模擬同學 Colab 裡的執行方式)
    # 注意：這裡的 python 或 micromamba 路徑需替換為伺服器上的實際路徑
    cmd = [
        "micromamba", "run", "-n", "trufor", 
        "python", "TruFor/TruFor_train_test/test.py",
        "-g", "0",
        "-in", tmp_in_dir,
        "-out", tmp_out_dir,
        "-exp", "trufor_ph3",
        "TEST.MODEL_FILE", "TruFor/TruFor_train_test/pretrained_models/trufor.pth.tar"
    ]
    
    # 3. 執行外部 TruFor 程式 (阻塞直到跑完)
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print(f"TruFor 執行失敗: {e.stderr.decode()}")
        return {"trufor_score": 0.0, "is_tampered": False}
        
    # 4. 讀取 TruFor 產生的 .npz 檔案以取得分數
    npz_path = os.path.join(tmp_out_dir, "temp_img.jpg.npz")
    if os.path.exists(npz_path):
        res = np.load(npz_path)
        score = float(res["score"]) # 獲取全域完整性得分
    else:
        score = 0.0

    # 5. 回傳符合 M1 介面契約的字典
    threshold = config.get("trufor_threshold", 0.5)
    return {
        "trufor_score": score,
        "is_tampered": score > threshold
    }