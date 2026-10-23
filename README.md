# Dashboard Kantor Baru SVO Yogyakarta

Situs statis (GitHub Pages) berisi: ringkasan dana, skema iuran DE/JD, status pembayaran per orang,
galeri desain (Render Interior III), dan progres renovasi.

- Live: https://zainalrauf862.github.io/kantor-svo-jogja/  (publik tanpa password; tidak diindeks mesin pencari lewat meta `noindex` — robots.txt di subfolder Pages tidak dibaca crawler)
- Sumber awal data: "Dashboard Dana Kantor SVO Yogyakarta - 23 Oktober 2026.md",
  "Render Interior III - SVO Yogyakarta 19 Okt 2026.pdf", dan ekspor chat WA grup "PROJECT INTERIOR SVO"
  (kontraktor PT HWG Arsitek) untuk timeline renovasi s/d laporan 22 Okt 2026.

## Struktur

| File | Isi |
|---|---|
| `template.html` | Tampilan + logika (HTML/CSS/JS, tanpa library) |
| `data/iuran.json` | Anggota (kewajiban & rinciannya) + **buku pembayaran** (`pembayaran`) |
| `data/desain.json` | Daftar area & gambar render |
| `data/renovasi.json` | Timeline progres (terbaru di atas) + foto |
| `build.py` | Cek konsistensi angka, lalu tulis `index.html` (data ditanam di dalamnya) |
| `alat/foto_progres.py` | Tambah entri progres + ubah foto ke WebP 640/1600 px |
| `img/desain/`, `img/progres/` | Gambar `<nama>-640.webp` dan `<nama>-1600.webp` |

Status (Lunas / Sebagian / Belum bayar), total dibayar, dan sisa **dihitung otomatis** dari
`pembayaran`. Jangan isi kolom dibayar/sisa secara manual.

## Cara update

1. **Pembayaran baru** — tambahkan baris di PALING BAWAH `data/iuran.json` → `pembayaran` (urut tanggal dicatat):
   `{"tanggal": "2026-10-24", "nama": "<nama persis seperti di anggota>", "nominal": 10000000, "keterangan": ""}`
   Ubah juga `posisi_data` ke tanggal terbaru. Dua pembayaran sama persis di hari yang sama → beri keterangan
   berbeda ("Pembayaran ke-1"/"ke-2"). Bayar lebih dari kewajiban → tambah `"lebih_ok": true`.
   Pembayaran berupa barang/jasa langsung (bukan uang ke kas) → `"langsung": true, "langsung_untuk": "..."`
   (muncul sebagai catatan di bawah angka terkumpul).
2. **Subsidi kantor diterima** — isi `subsidi_kantor.diterima` (angka, ≤ nominal) dan `status` berupa frasa
   huruf kecil yang pas di kalimat "Subsidi kantor RpX <status>.", mis. "sudah diterima".
3. **Progres renovasi** — `data/renovasi.json`:
   - `entri` (terbaru di atas): `{"tanggal", "judul", "tahap", "isi"?, "poin": [..]?, "link": "<tab>"?, "foto": [..]}`
   - `kondisi.area[]` (status: selesai / berjalan / persiapan), `berikutnya[]`, `keputusan[]`.
   - Foto: sekali saja `python3 -m venv ~/.venv-svo && ~/.venv-svo/bin/pip install pillow`, lalu
     `~/.venv-svo/bin/python alat/foto_progres.py 2026-10-30 "Judul" foto1.jpg "foto2.jpg=Keterangan" --isi "..." --tahap "Sipil"`
   - Saring foto dari grup kontraktor: JANGAN pasang foto orang tunawisma/ODGJ di gerbang, wajah pekerja close-up,
     plat nomor, label harga, bukti transfer, screenshot chat, atau proyek klien lain. Info harga RAB / fee
     tidak ditampilkan kecuali pemilik minta.
4. Jalankan `python3 build.py` (GAGAL kalau nama salah ketik, tanggal bukan YYYY-MM-DD, baris ganda,
   bayar > kewajiban, atau angka tidak konsisten).
5. Commit & push ke `main` → GitHub Pages memperbarui dalam ±1 menit (cache browser ±10 menit).

Kalau ada perubahan kewajiban/anggota (simulasi baru), ubah `anggota` di `data/iuran.json`
(`posisi` persis Komitmen/DE/JD, `grup` G1/G2/-, field opsional: `panggilan`, `tarif_lama`, `luar_struktur`, `catatan`):
`kewajiban = iuran_pribadi + tanggungan + komitmen_budget` dan
`tanggungan = staff × tarif_staff + jd_bawah × tarif_jd` — `build.py` mengecek keduanya, dan
total kewajiban + subsidi harus sama dengan `target`.
