import os
import sys

# 確保程式能找到 src 資料夾裡的核心模組
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from core.image_io import load_image
from core.preprocess import preprocess_image
from PIL import Image

def main():
    input_dir = "test_images"
    output_dir = "test_outputs"
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 1. 收集所有【本機圖片路徑】
    sources = []
    if os.path.exists(input_dir):
        for filename in os.listdir(input_dir):
            if not filename.startswith("."): # 排除隱藏檔
                sources.append(os.path.join(input_dir, filename))
    else:
        print(f"⚠️ 找不到 {input_dir} 資料夾，將跳過本機圖片測試。")

    # 2. 加上所有要測試的【網路 URL】
    test_urls = [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/42/Shaqi_jrvej.jpg/800px-Shaqi_jrvej.jpg",
        "https://www.python.org/static/community_logos/python-logo-master-v3-TM.png", # 驗證透明去背
        "https://this-is-a-fake-url.com/fake_image.jpg" # 驗證錯誤攔截
    ]
    sources.extend(test_urls)

    # 3. 統一開始跑迴圈測試！(這就是封裝的好處，邏輯只要寫一次)
    print(f"🚀 準備測試 {len(sources)} 個圖片來源...\n" + "-"*30)

    for i, source in enumerate(sources):
        print(f"\n[測試 {i+1}] 來源: {source[:60]}{'...' if len(source)>60 else ''}")

        try:
            # 載入 -> 前處理 -> 印出 shape
            raw_img = load_image(source)
            processed_img_array = preprocess_image(raw_img, max_size=1000)
            print(f"  ✨ [處理成功] 輸出矩陣形狀 (H, W, C): {processed_img_array.shape}")

            # 決定存檔檔名 (判斷是本機還是網址)
            if source.startswith("http"):
                save_name = f"test_{i+1}_url.jpg"
            else:
                base_name = os.path.basename(source).rsplit('.', 1)[0]
                save_name = f"test_{i+1}_local_{base_name}.jpg"
                
            save_path = os.path.join(output_dir, save_name)
            
            # 存檔供肉眼驗證
            Image.fromarray(processed_img_array).save(save_path, "JPEG")
            print(f"  ✅ 已儲存至: {save_path}")

        except Exception as e:
            print(f"  ❌ 處理失敗 (預期內的防呆機制): {e}")

if __name__ == "__main__":
    main()