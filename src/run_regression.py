# run_regression.py
import os
import sys
import glob
import time
import csv
import yaml

# 確保 Python 能找到 src 底下的模組 (根據你的專案路徑可微調)
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
sys.path.append('.') 

# 匯入 A 組核心架構
from core.image_io import load_image
from core.preprocess import preprocess_image
from core.router import route_and_execute
from core.quality_gate import check_image_quality

# 匯入 B/C 組各個模組
import modules.b_yolo
import modules.b_scrfd
import modules.c_ocr
# import modules.b_trufor  # 有接上就可以打開

def run_regression(test_dir="mini", report_path="report.csv"):
    print(f"\n🔍 尋找測試圖庫：{test_dir} ...")
    image_paths = glob.glob(os.path.join(test_dir, "*.*"))
    
    if not image_paths:
        print(f"❌ 找不到圖片！請確認 {test_dir} 資料夾存在且有圖片。")
        return

    print(f"🚀 開始執行 W6 回歸測試... 共 {len(image_paths)} 張圖片\n")

    # 讀取設定檔
    with open("config.yaml", 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    results = []
    total_start_time = time.time()
    success_count = 0
    gate_block_count = 0

    # 批次測試迴圈
    for img_path in image_paths:
        img_name = os.path.basename(img_path)
        start_time = time.time()
        status = "unknown"
        note = ""

        try:
            # 1. 載入與前處理
            raw_img = load_image(img_path)
            img_array = preprocess_image(raw_img, max_size=config["system"]["max_image_size"])
            
            # 2. 畫質守門員
            gate_result = check_image_quality(img_array, config)
            
            if not gate_result["is_valid"]:
                status = "REJECTED"
                gate_block_count += 1
                note = f"畫質攔截: {gate_result['reasons']}"
            else:
                # 3. 進入 AI 分流
                route_and_execute(img_array, config)
                status = "SUCCESS"
                success_count += 1
                note = "產線執行成功"

        except Exception as e:
            status = "ERROR"
            note = f"系統崩潰: {str(e)}"

        finally:
            # 結算單張耗時
            elapsed_time = time.time() - start_time
            results.append([img_name, status, f"{elapsed_time:.3f}", note])
            
            # 在終端機印出進度
            if status == "SUCCESS":
                print(f"  ✅ [{status}] {img_name} - 耗時: {elapsed_time:.3f}s")
            elif status == "REJECTED":
                print(f"  🛡️ [{status}] {img_name} - 耗時: {elapsed_time:.3f}s ({note})")
            else:
                print(f"  ❌ [{status}] {img_name} - 耗時: {elapsed_time:.3f}s ({note})")

    total_time = time.time() - total_start_time

    # 寫入 CSV 報表 (使用 utf-8-sig 讓 Excel 開啟不亂碼)
    with open(report_path, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["圖片檔名", "測試狀態", "耗時(秒)", "系統備註"])
        writer.writerows(results)

    # 印出最終統計報表
    print("\n" + "="*50)
    print("📊 W6 回歸測試報表 (Regression Report)")
    print("="*50)
    print(f"總測試數量：{len(image_paths)} 張")
    print(f"✅ 成功通過：{success_count} 張")
    print(f"🛡️ 合法攔截：{gate_block_count} 張 (Quality Gate)")
    print(f"❌ 系統錯誤：{len(image_paths) - success_count - gate_block_count} 張")
    print(f"⏱️ 總耗時　：{total_time:.2f} 秒")
    print(f"⏱️ 平均耗時：{total_time/len(image_paths):.2f} 秒/張")
    print(f"\n📂 報表已生成：{report_path}")

if __name__ == "__main__":
    # 你可以依據 Colab 真實路徑修改這裡
    run_regression(test_dir="mini", report_path="report.csv")   