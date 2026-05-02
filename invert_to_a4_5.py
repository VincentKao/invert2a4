"""
invert_to_a4.py
---------------
將圖片進行黑白反轉，放大指定倍數，並輸出為 A4 列印尺寸（300 DPI）。
若放大後超出單頁，自動分頁輸出（page_1, page_2 ...）。

用法：
    python3 invert_to_a4.py <輸入圖片> [輸出前綴] [--scale 倍數]
    python3 invert_to_a4.py --scan [資料夾路徑] [--scale 倍數]

範例：
    python3 invert_to_a4.py input.png                    # 單檔處理，自動單頁最大化
    python3 invert_to_a4.py input.png output --scale 3   # 3x 放大
    python3 invert_to_a4.py --scan                       # 掃描程式所在資料夾，補齊缺少的 inverted 檔
    python3 invert_to_a4.py --scan /path/to/folder       # 掃描指定資料夾
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


def autocrop(img: Image.Image, padding_px: int = 40) -> Image.Image:
    """自動裁切四周純白邊框，保留內容區域並加上 padding。"""
    arr  = np.array(img)
    # 找出非白色像素的行列範圍
    mask = ~(arr == 255).all(axis=2)
    rows = np.any(mask, axis=1)
    cols = np.any(mask, axis=0)
    if not rows.any():
        return img  # 全白圖，直接返回
    r0, r1 = np.where(rows)[0][[0, -1]]
    c0, c1 = np.where(cols)[0][[0, -1]]
    h, w   = arr.shape[:2]
    r0 = max(0, r0 - padding_px)
    r1 = min(h, r1 + padding_px)
    c0 = max(0, c0 - padding_px)
    c1 = min(w, c1 + padding_px)
    return img.crop((c0, r0, c1, r1))


def slice_to_pages(img: Image.Image, output_prefix: str) -> list:
    src_w, src_h = img.size
    total_pages  = (src_h + CONTENT_H - 1) // CONTENT_H
    saved_files  = []

    for page in range(total_pages):
        y_start = page * CONTENT_H
        y_end   = min(y_start + CONTENT_H, src_h)
        strip   = img.crop((0, y_start, src_w, y_end))

        canvas   = Image.new("RGB", (A4_W_PX, A4_H_PX), "white")
        x_offset = MARGIN_PX  # 靠左對齊
        canvas.paste(strip, (x_offset, MARGIN_PX))

        fname = f"{output_prefix}.png" if total_pages == 1 else f"{output_prefix}_page{page + 1}.png"
        canvas.save(fname, dpi=(DPI, DPI))
        saved_files.append(fname)

    return saved_files


def process(input_path: str, output_prefix: str, scale: float = None) -> None:
    img      = Image.open(input_path).convert("RGB")
    inverted = binarize_and_invert(img)

    # 先自動裁去四周空白，讓縮放以實際內容為準
    inverted = autocrop(inverted)
    src_w, src_h = inverted.size

    # 基準縮放：等比縮放至剛好填滿 A4（寬或高取小值，確保單頁不溢出）
    base_scale = min(CONTENT_W / src_w, CONTENT_H / src_h)

    if scale is None:
        # 自動模式：在不增加頁數的前提下最大化
        # 等比縮放，寬高同步放大，找出兩個方向都不超出的最大倍率
        max_scale  = min(CONTENT_W / (src_w * base_scale),
                         CONTENT_H / (src_h * base_scale))
        scale = max_scale
        print(f"   自動倍率：{scale:.3f}x（單頁最大，不增加頁數）")

    # 等比縮放（寬高同倍率）
    final_scale = base_scale * scale
    new_w = round(src_w * final_scale)
    new_h = round(src_h * final_scale)

    resized = inverted.resize((new_w, new_h), Image.LANCZOS)

    # 若寬度超出 A4，等比縮回（autocrop 後通常不會發生）
    if new_w > CONTENT_W:
        ratio   = CONTENT_W / new_w
        new_w   = CONTENT_W
        new_h   = round(new_h * ratio)
        resized = resized.resize((new_w, new_h), Image.LANCZOS)

    saved = slice_to_pages(resized, output_prefix)

    print(f"✅ 完成！共輸出 {len(saved)} 頁：")
    for f in saved:
        print(f"   {f}")
    print(f"   內容尺寸：{new_w} x {new_h} px（等比放大 {scale:.3f}x）")


def has_inverted(stem: str) -> bool:
    """判斷某個 stem 是否已有對應的 inverted 輸出（單頁或任意分頁）。"""
    prefix = stem + "_a4_inverted"
    folder = os.path.dirname(stem) or "."
    base   = os.path.basename(prefix)
    for name in os.listdir(folder):
        if name.startswith(base) and name.endswith(".png"):
            return True
    return False


def scan_and_process(folder: str, scale: float = None) -> None:
    folder = os.path.abspath(folder)
    if not os.path.isdir(folder):
        print(f"❌ 找不到資料夾：{folder}")
        sys.exit(1)

    all_pngs = sorted(
        f for f in os.listdir(folder)
        if f.lower().endswith(".png") and "_a4_inverted" not in f
    )

    if not all_pngs:
        print(f"📂 資料夾內沒有來源 PNG：{folder}")
        return

    missing = [f for f in all_pngs if not has_inverted(os.path.join(folder, os.path.splitext(f)[0]))]

    print(f"📂 掃描資料夾：{folder}")
    print(f"   來源 PNG：{len(all_pngs)} 個，缺少 inverted：{len(missing)} 個")

    if not missing:
        print("✅ 所有檔案都已有對應的 inverted 版本，無需處理。")
        return

    for i, fname in enumerate(missing, 1):
        input_path    = os.path.join(folder, fname)
        stem          = os.path.splitext(input_path)[0]
        output_prefix = stem + "_a4_inverted"
        print(f"\n[{i}/{len(missing)}] 處理：{fname}")
        try:
            process(input_path, output_prefix, scale)
        except Exception as e:
            print(f"   ❌ 失敗：{e}")


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)

    scale = None
    if "--scale" in args:
        idx   = args.index("--scale")
        scale = float(args[idx + 1])
        args  = [a for i, a in enumerate(args) if i not in (idx, idx + 1)]

    if args[0] == "--scan":
        folder = args[1] if len(args) >= 2 else os.path.dirname(os.path.abspath(__file__))
        scan_and_process(folder, scale)
        return

    input_path    = args[0]
    output_prefix = args[1] if len(args) >= 2 else os.path.splitext(input_path)[0] + "_a4_inverted"

    if not os.path.exists(input_path):
        print(f"❌ 找不到檔案：{input_path}")
        sys.exit(1)

    process(input_path, output_prefix, scale)


if __name__ == "__main__":
    main()
