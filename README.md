# invert2a4

將圖片進行黑白反轉，並輸出為 A4 列印尺寸（300 DPI）的 PNG 檔案。適合用於將手寫筆記、掃描文件或黑底白字的圖片，轉換成方便列印的白底黑字格式。

---

## 功能特色

- **Otsu 自動二值化**：自動計算最佳閾值，無需手動調整，適應不同光線與背景
- **黑白反轉**：將黑底白字轉為白底黑字（節省墨水、適合列印）
- **自動裁切空白邊框**：處理前先去除四周多餘空白，以實際內容為縮放基準
- **A4 尺寸輸出**：300 DPI，符合標準列印規格（2480 × 3508 px）
- **自動分頁**：圖片過長時自動切割為多頁輸出
- **批次掃描模式**：自動偵測資料夾內缺少 inverted 版本的圖片並補齊

---

## 環境需求

- Python 3.8+
- [Pillow](https://pillow.readthedocs.io/)
- [NumPy](https://numpy.org/)

安裝相依套件：

```bash
pip install Pillow numpy
```

---

## 使用方式

### 單檔處理

```bash
python3 invert_to_a4_5.py <輸入圖片> [輸出前綴] [--scale 倍數]
```

| 參數 | 說明 |
|---|---|
| `<輸入圖片>` | 來源 PNG 路徑（必填） |
| `[輸出前綴]` | 輸出檔案前綴（選填，預設為 `原檔名_a4_inverted`） |
| `--scale 倍數` | 縮放倍率（選填，預設自動計算單頁最大化） |

**範例：**

```bash
# 自動縮放，單頁最大化
python3 invert_to_a4_5.py input.png

# 指定輸出前綴
python3 invert_to_a4_5.py input.png output

# 放大 2 倍（可能分頁）
python3 invert_to_a4_5.py input.png output --scale 2
```

### 批次掃描模式

自動掃描指定資料夾，找出尚未有 inverted 版本的圖片並逐一處理：

```bash
python3 invert_to_a4_5.py --scan [資料夾路徑] [--scale 倍數]
```

| 參數 | 說明 |
|---|---|
| `--scan` | 啟用掃描模式（不指定路徑時，預設為程式所在資料夾） |
| `[資料夾路徑]` | 要掃描的資料夾路徑（選填） |
| `--scale 倍數` | 縮放倍率（選填） |

**範例：**

```bash
# 掃描程式所在資料夾，補齊所有缺少的 inverted 檔
python3 invert_to_a4_5.py --scan

# 掃描指定資料夾
python3 invert_to_a4_5.py --scan /path/to/images

# 掃描並指定 1.5 倍放大
python3 invert_to_a4_5.py --scan --scale 1.5
```

---

## 輸出命名規則

| 情況 | 輸出檔名 |
|---|---|
| 單頁 | `原檔名_a4_inverted.png` |
| 多頁（第 1 頁） | `原檔名_a4_inverted_page1.png` |
| 多頁（第 2 頁） | `原檔名_a4_inverted_page2.png` |

批次掃描時，程式會同時偵測單頁與多頁格式，已存在任一版本即視為已處理，不會重複執行。

---

## 技術細節

| 項目 | 規格 |
|---|---|
| 輸出 DPI | 300 |
| A4 尺寸 | 210 × 297 mm（2480 × 3508 px） |
| 邊距 | 10 mm（118 px） |
| 可用內容區域 | 2244 × 3272 px |
| 縮放演算法 | Lanczos（高品質降採樣） |
| 二值化方法 | Otsu's Method（自動閾值） |

---

## 檔案說明

| 檔案 | 說明 |
|---|---|
| `invert_to_a4_5.py` | 最新版本（含批次掃描功能） |
| `invert_to_a4_4.py` | 前一版本 |
| `invert_to_a4.py` ～ `invert_to_a4_3.py` | 歷史版本 |
