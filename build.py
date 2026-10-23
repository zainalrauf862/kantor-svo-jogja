#!/usr/bin/env python3
"""Gabungkan template.html + data/*.json -> index.html, sambil mengecek semua angka.

Pakai:  python3 build.py
Gagal (exit 1) kalau ada data yang tidak konsisten, supaya angka salah tidak ikut online.
"""
import datetime, json, os, re, sys
from decimal import Decimal, ROUND_HALF_UP

ROOT = os.path.dirname(os.path.abspath(__file__))
D = lambda *p: os.path.join(ROOT, *p)
err = []


def load(name):
    with open(D("data", name), encoding="utf-8") as f:
        return json.load(f)


iu, ds, rv = load("iuran.json"), load("desain.json"), load("renovasi.json")


def okdate(s):
    try:
        return isinstance(s, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", s) and datetime.date.fromisoformat(s)
    except ValueError:
        return False


def nonneg_int(v):
    return isinstance(v, int) and not isinstance(v, bool) and v >= 0

# ---------- cek data iuran ----------
names = [a["nama"] for a in iu["anggota"]]
if len(set(names)) != len(names):
    err.append("Ada nama anggota ganda.")
paid = {}
seen = set()
prev = ""
for p in iu["pembayaran"]:
    if p["nama"] not in names:
        err.append(f"Pembayaran atas nama '{p['nama']}' tidak ada di daftar anggota (cek ejaan).")
    if not nonneg_int(p["nominal"]) or p["nominal"] <= 0:
        err.append(f"Nominal pembayaran tidak valid: {p}")
    if not okdate(p["tanggal"]):
        err.append(f"Format tanggal harus YYYY-MM-DD: {p}")
    elif p["tanggal"] < prev:
        err.append(f"Pembayaran harus urut tanggal (baris baru di PALING BAWAH): {p}")
    else:
        prev = p["tanggal"]
    key = (p["tanggal"], p["nama"], p["nominal"], p.get("keterangan", ""))
    if key in seen and not p.get("duplikat_ok"):
        err.append(f"Baris pembayaran ganda (sama persis): {p}. Kalau memang 2x bayar, beri keterangan berbeda.")
    seen.add(key)
    paid[p["nama"]] = paid.get(p["nama"], 0) + p["nominal"]
if not okdate(iu.get("posisi_data")):
    err.append("posisi_data harus YYYY-MM-DD.")
elif prev and iu["posisi_data"] < prev:
    err.append(f"posisi_data ({iu['posisi_data']}) lebih lama dari pembayaran terakhir ({prev}).")
sk = iu["subsidi_kantor"]
if not nonneg_int(sk.get("diterima", 0)) or sk.get("diterima", 0) > sk["nominal"]:
    err.append("subsidi_kantor.diterima harus angka 0..nominal.")

NUM = ("staff", "jd_bawah", "de_bawah", "iuran_pribadi", "tarif_staff", "tarif_jd", "tanggungan", "komitmen_budget", "kewajiban")
for a in iu["anggota"]:
    if a["posisi"] not in ("Komitmen", "DE", "JD"):
        err.append(f"{a['nama']}: posisi harus Komitmen / DE / JD.")
    if a["grup"] not in ("G1", "G2", "-"):
        err.append(f"{a['nama']}: grup harus G1 / G2 / -.")
    bad = [k for k in NUM if not nonneg_int(a.get(k))]
    if bad:
        err.append(f"{a['nama']}: field harus angka bulat >= 0: {bad}")
        continue
    if a["kewajiban"] <= 0:
        err.append(f"{a['nama']}: kewajiban harus > 0.")
    t = a["staff"] * a["tarif_staff"] + a["jd_bawah"] * a["tarif_jd"]
    if t != a["tanggungan"]:
        err.append(f"{a['nama']}: tanggungan {a['tanggungan']} != staff×tarif + JD×tarif ({t})")
    k = a["iuran_pribadi"] + a["tanggungan"] + a["komitmen_budget"]
    if k != a["kewajiban"]:
        err.append(f"{a['nama']}: kewajiban {a['kewajiban']} != pribadi + tanggungan + komitmen ({k})")
    if paid.get(a["nama"], 0) > a["kewajiban"]:
        if any(p.get("lebih_ok") for p in iu["pembayaran"] if p["nama"] == a["nama"]):
            print(f"  catatan: {a['nama']} membayar lebih dari kewajiban (lebih_ok).")
        else:
            err.append(f"{a['nama']}: total bayar {paid[a['nama']]} > kewajiban {a['kewajiban']}. Cek baris ganda; kalau memang lebih, beri \"lebih_ok\": true.")

tot_kew = sum(a["kewajiban"] for a in iu["anggota"])
if tot_kew + iu["subsidi_kantor"]["nominal"] != iu["target"]:
    err.append(f"Total kewajiban {tot_kew} + subsidi {iu['subsidi_kantor']['nominal']} != target {iu['target']}")

masuk = sum(p["nominal"] for p in iu["pembayaran"])
sisa = sum(max(0, a["kewajiban"] - paid.get(a["nama"], 0)) for a in iu["anggota"])
st = {"Lunas": 0, "Sebagian": 0, "Belum bayar": 0}
for a in iu["anggota"]:
    d = paid.get(a["nama"], 0)
    st["Lunas" if d >= a["kewajiban"] else "Sebagian" if d else "Belum bayar"] += 1

# ---------- cek gambar ----------
for a in ds["area"]:
    for g in a["gambar"]:
        for w in (640, 1600):
            if not os.path.exists(D("img", "desain", f"{g['f']}-{w}.webp")):
                err.append(f"Gambar desain hilang: img/desain/{g['f']}-{w}.webp")
for e in rv["entri"]:
    for f in e.get("foto", []):
        for w in (640, 1600):
            if not os.path.exists(D("img", "progres", f"{f['f']}-{w}.webp")):
                err.append(f"Foto progres hilang: img/progres/{f['f']}-{w}.webp")
dates = [e["tanggal"] for e in rv["entri"]]
for d in dates + [ds.get("tanggal")] + [k["tanggal"] for k in rv.get("keputusan", [])] + ([rv["kondisi"]["per_tanggal"]] if rv.get("kondisi") else []):
    if not okdate(d):
        err.append(f"Tanggal tidak valid (harus YYYY-MM-DD): {d}")
if dates != sorted(dates, reverse=True):
    err.append("Entri renovasi harus urut dari tanggal terbaru ke terlama.")
for k in (rv.get("kondisi") or {}).get("area", []):
    if k.get("status") not in ("selesai", "berjalan", "persiapan"):
        err.append(f"Status kondisi area harus selesai/berjalan/persiapan: {k}")
for e in rv["entri"]:
    if e.get("link") and e["link"] not in ("ringkasan", "skema", "pembayaran", "desain", "renovasi"):
        err.append(f"link entri renovasi tidak dikenal: {e['link']}")
for f in ("entrance-1", "workstation-3", "meeting-besar-3", "dapur-2"):
    if not os.path.exists(D("img", "desain", f"{f}-640.webp")):
        err.append(f"Gambar yang dipakai template hilang: img/desain/{f}-640.webp")

if err:
    print("GAGAL — data perlu diperbaiki dulu:")
    for e in err:
        print("  -", e)
    sys.exit(1)

# ---------- tulis index.html ----------
def rp(n):
    return "Rp" + f"{n:,}".replace(",", ".")


def rpk(n):
    for div, u, dp in ((10**9, " miliar", "0.001"), (10**6, " juta", "0.01")):
        if n >= div:
            v = (Decimal(n) / div).quantize(Decimal(dp), rounding=ROUND_HALF_UP)
            v = format(v, "f").rstrip("0").rstrip(".").replace(".", ",")
            return f"Rp{v}{u}"
    return rp(n)


BULAN = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]


def tgl_id(s):
    d = datetime.date.fromisoformat(s)
    return f"{d.day} {BULAN[d.month - 1]} {d.year}"


def js(o):
    return json.dumps(o, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


terkumpul = masuk + iu["subsidi_kantor"].get("diterima", 0)
html = open(D("template.html"), encoding="utf-8").read()
for k, v in {
    "/*DATA_IURAN*/": js(iu),
    "/*DATA_DESAIN*/": js(ds),
    "/*DATA_RENOVASI*/": js(rv),
    "/*OG_TERKUMPUL*/": rpk(terkumpul),
    "/*OG_TANGGAL*/": tgl_id(iu["posisi_data"]),
    "/*OG_TARGET*/": rpk(iu["target"]),
}.items():
    assert html.count(k) == 1, k
    html = html.replace(k, v)
with open(D("index.html"), "w", encoding="utf-8") as f:
    f.write(html)

print("OK — index.html dibuat")
print(f"  posisi data      : {iu['posisi_data']}")
print(f"  target           : {rp(iu['target'])}")
print(f"  total kewajiban  : {rp(tot_kew)}  ({len(names)} nama)")
print(f"  sudah masuk      : {rp(terkumpul)}  ({terkumpul / iu['target'] * 100:.1f}% target)")
print(f"  sisa kewajiban   : {rp(sisa)}")
print(f"  belum masuk      : {rp(iu['target'] - terkumpul)}")
print(f"  status           : {st}")
print(f"  render desain    : {sum(len(a['gambar']) for a in ds['area'])} gambar, {sum(1 for a in ds['area'] if a['gambar'])} area")
print(f"  entri renovasi   : {len(rv['entri'])} ({sum(len(e.get('foto', [])) for e in rv['entri'])} foto)")
