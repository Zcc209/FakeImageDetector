import os
import sys
import argparse
import yaml
import json
import logging
from datetime import datetime

# 將 src 加入路徑
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

# 在 main.py 頂部加入這些 import (這會觸發裝飾器，完成註冊)
from core.registry import list_modules
from core.router import route_and_execute
from core.image_io import load_image
from core.preprocess import preprocess_image

import modules.b_yolo
import modules.b_scrfd
import modules.c_ocr

# ==========================================
# 1. 系統初始化與 Log 設定
# ==========================================
def setup_logger(log_level_str):
    """設定日誌系統，同時輸出到終端機與 logs/ 資料夾"""
    if not os.path.exists("logs"):
        os.makedirs("logs")
        
    log_filename = datetime.now().strftime("logs/run_%Y%m%d.log")
    numeric_level = getattr(logging, log_level_str.upper(), logging.INFO)
    
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

# ==========================================
# 2. B 組與 C 組的替身模組 (Stubs)
# 作用：先寫死假資料，證明資料流(Pipeline)是通的
# ==========================================
def run_vision_stub(img_array, config_b) -> dict:
    """B 組視覺/鑑偽模組的入口 (Stub)"""
    logging.info("執行 B 組視覺模組推論 (Stub)...")
    return {
        "trufor_score": 0.85,
        "is_tampered": 0.85 > config_b.get("trufor_threshold", 0.5),
        "yolo_objects": [{"label": "person", "confidence": 0.9}],
        "scrfd_face_count": 1
    }

def run_content_stub(img_array, config_c) -> dict:
    """C 組內容/LLM模組的入口 (Stub)"""
    logging.info(f"執行 C 組內容模組推論 (Stub, 模型: {config_c.get('gemini_model')})...")
    return {
        "ocr_text": "測試假文字：急售遊戲帳號加Line",
        "dire_score": 0.1,
        "is_ai_generated": False,
        "gemini_summary": "這是系統自動產生的假摘要，測試系統流程用。",
        "risk_tags": ["測試標籤"]
    }

# ==========================================
# 3. 主程式流程 (Router & Pipeline)
# ==========================================
def main():
    # A. CLI 參數解析
    parser = argparse.ArgumentParser(description="專題假圖偵測系統 v1")
    parser.add_argument("source", type=str, help="圖片的本地路徑或 URL")
    parser.add_argument("--config", type=str, default="config.yaml", help="設定檔路徑")
    args = parser.parse_args()

    # B. 讀取設定檔
    with open(args.config, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # C. 初始化 Logger
    logger = setup_logger(config["system"]["log_level"])
    logger.info("="*40)
    logger.info(f"系統啟動！準備處理來源: {args.source}")

    # 建立輸出資料夾
    output_dir = config["system"]["output_dir"]
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # D. 核心 Pipeline 開始
    result = {
        "status": "success",
        "error_code": None,
        "metadata": {"source": args.source},
        "vision": {},
        "content": {}
    }

    try:
        logger.info("Step 1: 載入並前處理圖片...")
        raw_img = load_image(args.source)
        img_array = preprocess_image(raw_img, max_size=config["system"]["max_image_size"])
        result["metadata"]["processed_shape"] = list(img_array.shape)
        
        # 確認註冊表狀態
        logger.info(f"已掛載的模組: {list_modules()}")

        logger.info("Step 2 & 3: 進入 Router 動態分流與模組推論...")
        # 將 numpy array 與設定檔丟給 router，它會把所有 JSON 組合好還給你
        router_results = route_and_execute(img_array, config)
        
        # 把 router 整理好的結果塞進最終的 JSON
        result["vision"] = router_results["vision"]
        result["content"] = router_results["content"]

        logger.info("所有模組執行完畢！")

    except Exception as e:
        logger.error(f"系統執行失敗: {e}")
        result["status"] = "error"
        result["error_code"] = str(e)

    # E. 輸出 result.json
    # 決定輸出檔名 (用時間戳避免覆蓋)
    timestamp = datetime.now().strftime("%H%M%S")
    output_file = os.path.join(output_dir, f"result_{timestamp}.json")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        
    logger.info(f"結果已儲存至: {output_file}")
    logger.info("="*40)

if __name__ == "__main__":
    main()