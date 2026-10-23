#!/usr/bin/env python3
"""Tambah entri progres renovasi + fotonya ke data/renovasi.json.

Butuh Pillow (sekali saja):  python3 -m venv ~/.venv-svo && ~/.venv-svo/bin/pip install pillow
Pakai:
  ~/.venv-svo/bin/python alat/foto_progres.py 2026-10-30 "Bongkar partisi lama" \\
      --isi "Pekerjaan bongkar lantai 2 dimulai." --tahap "Sipil" \\
      foto1.jpg "foto2.jpg=Keterangan foto 2" ...
Setiap foto dibuat 2 ukuran WebP (640 & 1600 px) di img/progres/.
Kalau tanggal + judul sudah ada, foto ditambahkan ke entri itu.
Lalu jalankan: python3 build.py
"""
import argparse, json, os, re
from PIL import Image, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ap = argparse.ArgumentParser()
ap.add_argument("tanggal"); ap.add_argument("judul")
ap.add_argument("--isi", default=""); ap.add_argument("--tahap", default="")
ap.add_argument("foto", nargs="*")
a = ap.parse_intermixed_args()
assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", a.tanggal), "tanggal harus YYYY-MM-DD"

path = os.path.join(ROOT, "data", "renovasi.json")
data = json.load(open(path, encoding="utf-8"))
ent = next((e for e in data["entri"] if e["tanggal"] == a.tanggal and e["judul"] == a.judul), None)
if not ent:
    ent = {"tanggal": a.tanggal, "judul": a.judul, "isi": a.isi, "tahap": a.tahap, "foto": []}
    data["entri"].append(ent)
else:
    if a.isi: ent["isi"] = a.isi
    if a.tahap: ent["tahap"] = a.tahap
slug = re.sub(r"[^a-z0-9]+", "-", a.judul.lower()).strip("-")[:40]
outdir = os.path.join(ROOT, "img", "progres"); os.makedirs(outdir, exist_ok=True)
for spec in a.foto:
    src, _, ket = spec.partition("=")
    n = len(ent["foto"]) + 1
    base = f"{a.tanggal}-{slug}-{n}"
    while os.path.exists(os.path.join(outdir, f"{base}-640.webp")):
        n += 1; base = f"{a.tanggal}-{slug}-{n}"
    im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    for w, q in ((640, 76), (1600, 82)):
        c = im.copy()
        if c.width > w:
            c = c.resize((w, round(c.height * w / c.width)), Image.LANCZOS)
        c.save(os.path.join(outdir, f"{base}-{w}.webp"), "WEBP", quality=q, method=6)
    big = Image.open(os.path.join(outdir, f"{base}-1600.webp"))
    ent["foto"].append({"f": base, "ket": ket.strip(), "w": big.width, "h": big.height})
    print("  +", base)
data["entri"].sort(key=lambda e: e["tanggal"], reverse=True)
json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("OK — entri:", a.tanggal, a.judul, f"({len(ent['foto'])} foto)")
