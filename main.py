import os
import sys
import argparse
import yaml
import json
import logging
from datetime import datetime
from urllib.parse import urlparse # 用來判斷是不是 URL

# 將 src 加入路徑
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

# 在 main.py 頂部加入這些 import (這會觸發裝飾器，完成註冊)
from core.registry import list_modules
from core.router import route_and_execute
from core.image_io import load_image, load_image_from_bytes # 確保你有這個從 bytes 讀取的函式
from core.preprocess import preprocess_image

# ======== W7 & W8 新增的 Import ========
from core.fetcher import fetch_image_from_url
from core.errors import AppError, ErrorCode, build_error_response
# =======================================

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
# 2. 主程式流程 (Router & Pipeline)
# ==========================================
def main():
    # A. CLI 參數解析
    parser = argparse.ArgumentParser(description="專題假圖偵測系統 v1")
    parser.add_argument("source", type=str, help="圖片的本地路徑或 URL")
    parser.add_argument("--config", type=str, default="config.yaml", help="設定檔路徑")
    # 新增一個開關，控制是否允許從網址抓圖 (配合 A8 需求)
    parser.add_argument("--disable-fetcher", action="store_true", help="停用從 URL 抓取圖片的功能")
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
    # 先準備好預設的成功 JSON 結構
    result = {
        "status": "success",
        "error_code": 0,
        "error_name": "SUCCESS",
        "message": "OK",
        "metadata": {"source": args.source, "is_url": False},
        "vision": {},
        "content": {}
    }

    try:
        logger.info("Step 1: 取得圖片...")
        
        # 簡單判斷 source 是否為 URL (http:// 或 https://)
        is_url = urlparse(args.source).scheme in ['http', 'https']
        result["metadata"]["is_url"] = is_url
        
        raw_img = None
        
        if is_url:
            if args.disable_fetcher:
                raise AppError(ErrorCode.INVALID_INPUT, "系統目前停用從 URL 抓取圖片的功能")
                
            logger.info(f"偵測到 URL 輸入，啟動 Fetcher 模組進行安全下載...")
            image_bytes = fetch_image_from_url(args.source)
            logger.info("下載完成，轉換為陣列格式...")
            # 這裡假設你的 image_io 裡有 load_image_from_bytes，
            # 如果沒有，你可能要把 bytes 存成暫存檔再用 load_image 讀取，或者擴充 image_io.py
            raw_img = load_image_from_bytes(image_bytes)
        else:
            logger.info(f"偵測到本地路徑，直接讀取...")
            raw_img = load_image(args.source)

        logger.info("Step 2: 圖片前處理...")
        img_array = preprocess_image(raw_img, max_size=config["system"]["max_image_size"])
        result["metadata"]["processed_shape"] = list(img_array.shape)
        
        # 確認註冊表狀態
        logger.info(f"已掛載的模組: {list_modules()}")

        logger.info("Step 3: 進入 Router 動態分流與模組推論...")
        # 將 numpy array 與設定檔丟給 router，它會把所有 JSON 組合好還給你
        router_results = route_and_execute(img_array, config)
        
        # 把 router 整理好的結果塞進最終的 JSON
        result["vision"] = router_results.get("vision", {})
        result["content"] = router_results.get("content", {})

        logger.info("所有模組執行完畢！")

    # ====== 使用 W7 的標準錯誤處理 ======
    except AppError as e:
        logger.error(f"系統執行發生已知錯誤 [{e.code.name}]: {e.message}")
        # 使用我們定義好的格式覆蓋 result
        result = build_error_response(e.code, e.message)
        result["metadata"] = {"source": args.source} # 保留來源資訊

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"系統發生未預期崩潰:\n{error_trace}")
        # 捕捉未知錯誤
        result = build_error_response(ErrorCode.UNKNOWN_ERROR, f"未預期錯誤: {str(e)}")
        result["metadata"] = {"source": args.source}

    # ====================================

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