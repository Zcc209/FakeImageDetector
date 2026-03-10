import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from core.image_io import load_image
from core.preprocess import preprocess_image

def test_preprocessing():
    # 我們拿剛剛那張 Python logo 來測，它是一張帶有透明背景的 PNG
    url = "https://www.python.org/static/community_logos/python-logo-master-v3-TM.png"
    
    print("1. 載入原始圖片...")
    raw_img = load_image(url)
    print(f"   原始狀態 -> 格式: {raw_img.mode}, 尺寸: {raw_img.size}")
    
    print("\n2. 執行前處理 (測試強制縮小到 max_size=300)...")
    # 我們故意把 max_size 設很小，來驗證縮放功能
    processed_img_array = preprocess_image(raw_img, max_size=300)
    
    # numpy array 用 .shape 看維度，會印出 (高度, 寬度, 通道數)
    print(f"   處理後狀態 -> 類型: numpy.ndarray, 形狀 (H, W, C): {processed_img_array.shape}")
    
    # 取得高、寬、通道數
    h, w, c = processed_img_array.shape
    
    # 驗證結果
    if c == 3:
        print("✅ 成功轉換為 3 通道 (RGB) 矩陣！(透明背景應該被補成白色了)")
    
    if max(h, w) <= 300:
        print(f"✅ 成功等比例縮放圖片！(目前最大邊為 {max(h, w)})")

if __name__ == "__main__":
    test_preprocessing()