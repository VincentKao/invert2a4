"""
invert_to_a4.py
---------------
將圖片進行黑白反轉，並調整為 A4 列印尺寸（300 DPI）。

用法：
    python invert_to_a4.py <輸入圖片> [輸出圖片]

若未指定輸出路徑，預設輸出為 <原檔名>_a4_inverted.png
"""

from PIL import Image, ImageOps
import sys
import os
import numpy as np


def _otsu_threshold(pixels: "np.ndarray") -> int:
    """計算 Otsu 最佳二值化門檻值（自動找到最能分離前景/背景的切割點）"""
    hist, _ = np.histogram(pixels.flatten(), bins=256, range=(0, 256))
    total = pixels.size
    sum_all = np.dot(np.arange(256), hist)
    sum_b, w_b, max_var, threshold = 0.0, 0.0, 0.0, 128
    for t in range(256):
        w_b += hist[t]
        if w_b == 0:
            continue
        w_f = total - w_b
        if w_f == 0:
            break
        sum_b += t * hist[t]
        m_b = sum_b / w_b
        m_f = (sum_all - sum_b) / w_f
        var = w_b * w_f * (m_b - m_f) ** 2
        if var > max_var:
            max_var, threshold = var, t
    return threshold

# ── A4 尺寸設定 ──────────────────────────────────────────
DPI = 300                          # 列印解析度
A4_W_MM, A4_H_MM = 210, 297       # A4 寬 x 高（毫米）
MARGIN_MM = 10                     # 四邊留白（毫米）

def mm_to_px(mm: float, dpi: int = DPI) -> int:
    return round(mm / 25.4 * dpi)

A4_W_PX = mm_to_px(A4_W_MM)       # 2480 px @ 300 DPI
A4_H_PX = mm_to_px(A4_H_MM)       # 3508 px @ 300 DPI
MARGIN_PX = mm_to_px(MARGIN_MM)


def invert_and_fit_a4(input_path: str, output_path: str) -> None:
    # 1. 開啟原圖
    img = Image.open(input_path).convert("RGB")

    # 2. 灰階化 → 二值化 → 反轉（深色背景＋淺色文字 → 白底黑字）
    gray = img.convert("L")                      # 轉灰階
    # Otsu 自動門檻：計算最佳切割點讓黑白分離最大化
    import numpy as np
    pixels = np.array(gray)
    threshold = _otsu_threshold(pixels)          # 自動決定門檻值
    bw = gray.point(lambda p: 255 if p > threshold else 0, "1")  # 二值化
    inverted = ImageOps.invert(bw.convert("RGB"))  # 反轉：深底→白，淺字→黑

    # 3. 計算在 A4 留白區域內的最大等比縮放尺寸
    content_w = A4_W_PX - 2 * MARGIN_PX
    content_h = A4_H_PX - 2 * MARGIN_PX

    src_w, src_h = inverted.size
    scale = min(content_w / src_w, content_h / src_h)
    new_w = round(src_w * scale)
    new_h = round(src_h * scale)

    resized = inverted.resize((new_w, new_h), Image.LANCZOS)

    # 4. 建立白底 A4 畫布，將圖片置中貼上
    canvas = Image.new("RGB", (A4_W_PX, A4_H_PX), "white")
    x_offset = (A4_W_PX - new_w) // 2
    y_offset = (A4_H_PX - new_h) // 2
    canvas.paste(resized, (x_offset, y_offset))

    # 5. 儲存，寫入 DPI 資訊（讓印表機正確辨識）
    canvas.save(output_path, dpi=(DPI, DPI))
    print(f"✅ 完成！輸出檔案：{output_path}")
    print(f"   尺寸：{A4_W_PX} x {A4_H_PX} px（{DPI} DPI = A4 {A4_W_MM}×{A4_H_MM} mm）")


def main():
    if len(sys.argv) < 2:
        print("用法：python invert_to_a4.py <輸入圖片> [輸出圖片]")
        sys.exit(1)

    input_path = sys.argv[1]

    if len(sys.argv) >= 3:
        output_path = sys.argv[2]
    else:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_a4_inverted.png"

    if not os.path.exists(input_path):
        print(f"❌ 找不到檔案：{input_path}")
        sys.exit(1)

    invert_and_fit_a4(input_path, output_path)


if __name__ == "__main__":
    main()
