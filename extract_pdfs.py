# extract_pdfs.py
import os
from glob import glob
import fitz  # PyMuPDF
import pdfplumber

PREF_DIR = "data/raw_pdfs"
ALT_DIR  = "data"
OUT_DIR  = "data/txt"

os.makedirs(OUT_DIR, exist_ok=True)

def pick_input_dir():
    cand = []
    if os.path.isdir(PREF_DIR):
        cand.append(PREF_DIR)
    if os.path.isdir(ALT_DIR):
        cand.append(ALT_DIR)
    for c in cand:
        pdfs = sorted(glob(os.path.join(c, "*.pdf")))
        if pdfs:
            print(f"📥 Using input directory: {c}  (found {len(pdfs)} PDF)")
            return c, pdfs
    raise FileNotFoundError(
        "❌ No PDFs found. Put files into 'data/raw_pdfs' (recommended) or 'data/'."
    )

def extract_with_pymupdf(pdf_path: str) -> str:
    text = []
    with fitz.open(pdf_path) as doc:
        for i, page in enumerate(doc, start=1):
            t = page.get_text("text")
            if t:
                text.append(t)
    return "\n".join(text).strip()

def extract_with_pdfplumber(pdf_path: str) -> str:
    text = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text() or ""
            if t:
                text.append(t)
    return "\n".join(text).strip()

def looks_like_scanned(pdf_path: str) -> bool:
    """粗略判断：如果两种引擎皆提不到字，多半是扫描件。"""
    try:
        if extract_with_pymupdf(pdf_path):
            return False
        if extract_with_pdfplumber(pdf_path):
            return False
        return True
    except Exception:
        return True

def convert_one(pdf_path: str) -> str:
    base = os.path.basename(pdf_path).rsplit(".", 1)[0]
    out_txt = os.path.join(OUT_DIR, base + ".txt")

    print(f"→ Converting: {os.path.basename(pdf_path)}")

    text = extract_with_pymupdf(pdf_path)
    if not text:
        print("  • PyMuPDF found 0 chars, trying pdfplumber…")
        text = extract_with_pdfplumber(pdf_path)

    if not text:
        if looks_like_scanned(pdf_path):
            ocr_flag = os.path.join(OUT_DIR, base + "_OCR_NEEDED.txt")
            open(ocr_flag, "w", encoding="utf-8").write(
                "This PDF looks like an image/scanned document. "
                "Please enable OCR workflow to extract text."
            )
            print(f"  ⚠️  No text found. Marked as scanned. Created: {ocr_flag}")
            return ocr_flag
        else:
            # 极端情况：不是扫描但也提不出
            open(out_txt, "w", encoding="utf-8").write("")
            print(f"  ⚠️  No text extracted. Wrote empty file: {out_txt}")
            return out_txt

    # 写出文本
    with open(out_txt, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"  ✅ Wrote: {out_txt}  ({len(text)} chars)")
    return out_txt

def main():
    in_dir, pdfs = pick_input_dir()
    ok, scan, empty = 0, 0, 0
    for p in pdfs:
        try:
            out = convert_one(p)
            if out.endswith("_OCR_NEEDED.txt"):
                scan += 1
            else:
                # 检查是否为空文本
                if os.path.getsize(out) == 0:
                    empty += 1
                else:
                    ok += 1
        except Exception as e:
            print(f"  ❌ Failed on {os.path.basename(p)}: {e}")

    print("\n===== SUMMARY =====")
    print(f"  Converted OK : {ok}")
    print(f"  OCR needed   : {scan}")
    print(f"  Empty text   : {empty}")
    print(f"  Output dir   : {OUT_DIR}")
    print("====================")

if __name__ == "__main__":
    main()