"""
invert_to_a4.py
---------------
將圖片進行黑白反轉，放大指定倍數，並輸出為 A4 列印尺寸（300 DPI）。
若放大後超出單頁，自動分頁輸出（page_1, page_2 ...）。

用法：
    python3 invert_to_a4.py <輸入圖片> [輸出前綴] [--scale 倍數]

範例：
    python3 invert_to_a4.py input.png                    # 預設 2x，自動分頁
    python3 invert_to_a4.py input.png output --scale 3   # 3x 放大
"""

from PIL import Image, ImageOps
import sys
import os
import numpy as np

# ── A4 尺寸設定 ──────────────────────────────────────────
DPI = 300
A4_W_MM, A4_H_MM = 210, 297
MARGIN_MM = 10

def mm_to_px(mm: float, dpi: int = DPI) -> int:
    return round(mm / 25.4 * dpi)

A4_W_PX   = mm_to_px(A4_W_MM)    # 2480 px
A4_H_PX   = mm_to_px(A4_H_MM)    # 3508 px
MARGIN_PX = mm_to_px(MARGIN_MM)
CONTENT_W = A4_W_PX - 2 * MARGIN_PX
CONTENT_H = A4_H_PX - 2 * MARGIN_PX


def _otsu_threshold(pixels: np.ndarray) -> int:
    hist, _ = np.histogram(pixels.flatten(), bins=256, range=(0, 256))
    total    = pixels.size
    sum_all  = np.dot(np.arange(256), hist)
    sum_b = w_b = max_var = 0.0
    threshold = 128
    for t in range(256):
        w_b += hist[t]
        if w_b == 0: continue
        w_f = total - w_b
        if w_f == 0: break
        sum_b += t * hist[t]
        m_b = sum_b / w_b
        m_f = (sum_all - sum_b) / w_f
        var = w_b * w_f * (m_b - m_f) ** 2
        if var > max_var:
            max_var, threshold = var, t
    return threshold


def binarize_and_invert(img: Image.Image) -> Image.Image:
    gray      = img.convert("L")
    threshold = _otsu_threshold(np.array(gray))
    bw        = gray.point(lambda p: 255 if p > threshold else 0, "1")
    return ImageOps.invert(bw.convert("RGB"))


def slice_to_pages(img: Image.Image, output_prefix: str) -> list:
    src_w, src_h = img.size
    total_pages  = (src_h + CONTENT_H - 1) // CONTENT_H
    saved_files  = []

    for page in range(total_pages):
        y_start = page * CONTENT_H
        y_end   = min(y_start + CONTENT_H, src_h)
        strip   = img.crop((0, y_start, src_w, y_end))

        canvas   = Image.new("RGB", (A4_W_PX, A4_H_PX), "white")
        x_offset = (A4_W_PX - src_w) // 2
        canvas.paste(strip, (x_offset, MARGIN_PX))

        fname = f"{output_prefix}.png" if total_pages == 1 else f"{output_prefix}_page{page + 1}.png"
        canvas.save(fname, dpi=(DPI, DPI))
        saved_files.append(fname)

    return saved_files


def process(input_path: str, output_prefix: str, scale: float = None) -> None:
    img      = Image.open(input_path).convert("RGB")
    inverted = binarize_and_invert(img)

    src_w, src_h = inverted.size
    fit_scale = CONTENT_W / src_w        # 基準：寬度剛好填滿 A4

    if scale is None:
        # 自動模式：同時考慮寬度與高度限制，找出不超過單頁的最大倍率
        # 寬度固定填滿 A4，只有高度限制倍率
        scale = CONTENT_H / (src_h * fit_scale)
        print(f"   自動倍率：{scale:.3f}x（單頁最大，不增加頁數）")

    new_w = CONTENT_W
    new_h = round(src_h * fit_scale * scale)

    resized = inverted.resize((new_w, new_h), Image.LANCZOS)
    saved   = slice_to_pages(resized, output_prefix)

    print(f"✅ 完成！共輸出 {len(saved)} 頁：")
    for f in saved:
        print(f"   {f}")
    print(f"   內容尺寸：{new_w} x {new_h} px（放大 {scale:.3f}x）")


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)

    scale = None  # 預設 None = 自動計算最大單頁倍率
    if "--scale" in args:
        idx   = args.index("--scale")
        scale = float(args[idx + 1])
        args  = [a for i, a in enumerate(args) if i not in (idx, idx + 1)]

    input_path = args[0]
    output_prefix = args[1] if len(args) >= 2 else os.path.splitext(input_path)[0] + "_a4_inverted"

    if not os.path.exists(input_path):
        print(f"❌ 找不到檔案：{input_path}")
        sys.exit(1)

    process(input_path, output_prefix, scale)


if __name__ == "__main__":
    main()
