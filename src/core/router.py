# src/core/router.py
import logging
from core.registry import get_module

logger = logging.getLogger(__name__)

def route_and_execute(img_array, config: dict) -> dict:
    """
    系統的路由中心。
    負責依序呼叫各個模組，並根據前一個模組的結果決定後續動作。
    """
    results = {"vision": {}, "content": {}}

    # ==========================================
    # 1. 執行基礎視覺模組 (YOLO)
    # ==========================================
    yolo_func = get_module("yolo")
    yolo_res = yolo_func(img_array, config.get("vision_b", {}))
    results["vision"].update(yolo_res)

    # ==========================================
    # 2. 條件分流 (Routing): 有人才抓臉
    # ==========================================
    # 檢查 YOLO 是否有偵測到 "person"
    objects = yolo_res.get("yolo_objects", [])
    has_person = any(obj.get("label") == "person" for obj in objects)

    if has_person:
        logger.info("-> [Router] YOLO 發現人物，觸發 SCRFD 人臉偵測。")
        scrfd_func = get_module("scrfd")
        results["vision"].update(scrfd_func(img_array, config.get("vision_b", {})))
    else:
        logger.info("-> [Router] 畫面無人，跳過 SCRFD 以節省算力。")
        results["vision"]["scrfd_face_count"] = 0

    # ==========================================
    # 3. 執行內容模組 (OCR 等)
    # ==========================================
    ocr_func = get_module("ocr")
    results["content"].update(ocr_func(img_array, config.get("content_c", {})))

    return results