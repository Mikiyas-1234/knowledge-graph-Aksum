"""OCR wrapper plus the measurements needed to decide whether an engine is good enough.

No engine is trusted for Geez until it is scored on your own scans: run `evaluate`
on pages that an expert has transcribed by hand.
"""
import shutil
import subprocess
import unicodedata

ETHIOPIC_RANGES = ((0x1200, 0x139F), (0x2D80, 0x2DDF), (0xAB00, 0xAB2F))


def is_ethiopic(ch):
    o = ord(ch)
    return any(lo <= o <= hi for lo, hi in ETHIOPIC_RANGES)


def ethiopic_ratio(text):
    """Share of letters that are Ethiopic. A low value on a Geez page means the engine failed."""
    letters = [c for c in text if c.isalpha()]
    return sum(map(is_ethiopic, letters)) / len(letters) if letters else 0.0


def _clean(text):
    return " ".join(unicodedata.normalize("NFC", text).split())


def edit_distance(a, b):
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def cer(reference, hypothesis):
    """Character error rate against an expert transcription (whitespace runs ignored)."""
    ref, hyp = _clean(reference), _clean(hypothesis)
    if not ref:
        raise ValueError("empty reference transcription")
    return edit_distance(ref, hyp) / len(ref)


class TesseractOcr:
    """Calls the `tesseract` binary. `lang` must be an installed model (check `tesseract --list-langs`)."""

    def __init__(self, lang="amh", binary="tesseract"):
        self.lang, self.binary = lang, binary

    def __call__(self, image_path):
        if shutil.which(self.binary) is None:
            raise RuntimeError(f"'{self.binary}' is not installed")
        out = subprocess.run([self.binary, image_path, "stdout", "-l", self.lang],
                             capture_output=True, text=True, check=True)
        return out.stdout


def evaluate(engine, pairs):
    """pairs: [(image_path, reference_text)]. Returns per-page results, worst page first."""
    results = []
    for path, ref in pairs:
        hyp = engine(path)
        results.append({"page": path, "cer": round(cer(ref, hyp), 4), "ethiopic_ratio": round(ethiopic_ratio(hyp), 3)})
    results.sort(key=lambda r: r["cer"], reverse=True)
    mean = sum(r["cer"] for r in results) / len(results) if results else None
    return {"mean_cer": None if mean is None else round(mean, 4), "pages": results}
