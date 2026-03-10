import sys
import os

# 把 src 資料夾加入系統路徑，這樣才能 import 到 core
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from core.image_io import load_image, ImageLoadError

def test_run():
    # 測試 1: 正常的網路圖片
    print("測試 1: 下載網路圖片...")
    url = "https://www.python.org/static/community_logos/python-logo-master-v3-TM.png"
    try:
        img = load_image(url)
        print(f"✅ 成功！格式: {img.format}, 尺寸: {img.size}")
    except ImageLoadError as e:
        print(f"❌ 失敗: {e}")

    # 測試 2: 故意給錯誤的路徑
    print("\n測試 2: 讀取不存在的本地圖片...")
    try:
        img = load_image("fake_path_123.jpg")
        print("❌ 失敗：不應該讀取成功才對")
    except ImageLoadError as e:
        print(f"✅ 成功攔截錯誤: {e}")

if __name__ == "__main__":
    test_run()