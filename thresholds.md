# 畫質把關機制 (Quality Gate) 門檻與原理說明 v1

本模組旨在 AI 模型推論前，攔截畫質極差（如模糊、過暗、解析度過低）的影像，以避免模型產出無效結果並節省運算資源。

## 評估指標與門檻表

| 檢查項目 | 判定演算法與原理 | 預設門檻值 | 退回原因代碼 (Reason) | 調整建議指南 |
| :--- | :--- | :--- | :--- | :--- |
| **解析度** | 檢查影像寬與高的像素值。 | 寬 < `150` <br> 高 < `150` | `low_resolution` | 依據 B 組 (YOLO/TruFor) 的最小輸入限制進行動態調整。 |
| **模糊度** | **Laplacian 變異數 (Variance of Laplacian)**<br>利用二階導數抓取影像邊緣。若圖片模糊，邊緣細節少，變異數會極低。 | 數值 < `100.0` | `too_blurry` | 若發現「正常的人臉圖」頻繁被擋下，可下調至 `50`~`80`。若要嚴格抓假圖，可上調。 |
| **低光/過暗** | **灰階平均值 (Mean Pixel Value)**<br>將 RGB 轉灰階，計算所有像素的平均亮度 (0~255)。 | 平均 < `30.0` | `too_dark` | 數值 30 代表幾乎全黑。如果應用場景多為夜間拍攝，可下調至 `15`。 |
| **過曝/全白** | 同上，計算灰階平均值。 | 平均 > `240.0` | `too_bright` | 數值 240 代表圖片幾乎全白，可防止惡意輸入全白雜訊圖。 |

## 系統輸出範例 (JSON)
當一張圖片被 Quality Gate 擋下時，系統將不會呼叫後續的 Router，而是直接回傳以下格式：
```json
{
  "status": "rejected",
  "error_message": "Image failed quality gate.",
  "gate_details": {
    "is_valid": false,
    "reasons": ["too_blurry", "too_dark"],
    "metrics": {
      "resolution": [800, 600],
      "blur_score": 45.12,
      "brightness": 25.4
    }
  }
}