# Auto Absen MagangHub

Biar gak panik kalau lupa absen MagangHub. Cukup satu perintah, program login, kirim absen, selesai. Data absen diambil dari berkas `.env` dan gak disimpan di mana pun.

Anggap program ini ban serep: dipakai saat kepepet, bukan tiap hari. Kalau ingat, absen sendiri tepat waktu.

> Program ini tanpa jaminan apa pun. Gunakan dengan risiko sendiri — lihat bagian [Peringatan](#peringatan).

Kalau program ini membantu Anda, pertimbangkan memberi ⭐ pada repositori ini.

## Daftar Isi

- [Auto Absen MagangHub](#auto-absen-maganghub)
  - [Daftar Isi](#daftar-isi)
  - [Memulai](#memulai)
    - [Cara Kerja](#cara-kerja)
    - [Prasyarat](#prasyarat)
    - [Instalasi](#instalasi)
    - [Konfigurasi](#konfigurasi)
    - [Penggunaan](#penggunaan)
  - [Penjadwalan Otomatis](#penjadwalan-otomatis)
    - [Task Scheduler (Windows)](#task-scheduler-windows)
    - [GitHub Actions](#github-actions)
  - [Notifikasi Telegram](#notifikasi-telegram)
  - [Informasi Proyek](#informasi-proyek)
    - [Struktur Proyek](#struktur-proyek)
    - [Keamanan](#keamanan)
    - [Peringatan](#peringatan)
    - [Kontribusi](#kontribusi)
    - [Atribusi](#atribusi)
    - [Lisensi](#lisensi)

## Memulai

### Cara Kerja

1. Program membaca berkas `.env`.
2. Program login ke SSO Kemnaker dengan kredensial (nama pengguna dan kata sandi) dari `.env`.
3. Program meminta `access token` dari API Monev.
4. Program mengirim permintaan POST ke `/attendances/with-daily-log` dengan status `PRESENT` dan log harian.
5. Bila login atau pengiriman gagal karena gangguan jaringan, program mencoba ulang maksimal 3 kali dengan jeda 1 menit.

### Prasyarat

- Python 3.10 atau versi lebih baru.
- Akun MagangHub (login Siap Kerja) beserta kata sandi.
- Penjadwalan lokal membutuhkan Windows. GitHub Actions tersedia sebagai alternatif tanpa Windows. Perintah manual berjalan di sistem operasi apa pun.

### Instalasi

1. Salin repositori ini.
2. Salin `.env.example` menjadi `.env`, lalu isi nilai setiap variabel.
3. Pasang dependensi dengan salah satu dari dua cara berikut.

**Cara A, dengan uv:**

1. Pasang uv:

   ```
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. Buat lingkungan virtual, lalu pasang dependensi:

   ```
   uv venv
   uv pip install -r requirements.txt
   ```

**Cara B, dengan pip:**

1. Buat lingkungan virtual:

   ```
   python -m venv .venv
   ```

2. Aktifkan lingkungan virtual:

   ```
   .venv\Scripts\activate
   ```

3. Pasang dependensi:

   ```
   pip install -r requirements.txt
   ```

### Konfigurasi

Berkas `.env` menyimpan seluruh konfigurasi. Tabel berikut memuat setiap variabel.

| Variabel | Wajib | Keterangan |
|---|---|---|
| `SIAPKERJA_USERNAME` | Ya | NIK, email, atau nomor telepon akun Anda |
| `SIAPKERJA_PASSWORD` | Ya | Kata sandi akun Anda |
| `CLOCK_IN_TIME` | Tidak | Jam tugas untuk penjadwalan otomatis, format `HH:MM`. Kosong berarti `16:00` |
| `HARI_LIBUR` | Tidak | Nama hari libur, pisahkan dengan koma. Nilai bawaan: `Sabtu,Minggu` |
| `LATITUDE` | Tidak | Lintang lokasi absen. Nilai bawaan: `-6.2088` |
| `LONGITUDE` | Tidak | Bujur lokasi absen. Nilai bawaan: `106.8456` |
| `LOCATION` | Tidak | Nama lokasi absen. Nilai bawaan: `Jakarta` |
| `ACTIVITY_LOG` | Ya | Isian kolom aktivitas harian |
| `LESSON_LEARNED` | Ya | Isian kolom pelajaran hari ini |
| `OBSTACLES` | Ya | Isian kolom kendala harian |
| `TELEGRAM_BOT_TOKEN` | Tidak | Token bot Telegram untuk notifikasi. Kosong berarti notifikasi mati |
| `TELEGRAM_CHAT_ID` | Tidak | ID chat Telegram tujuan notifikasi. Kosong berarti notifikasi mati |

Program juga membaca `API_BASE` dan `AUTH_BASE`. Nilai bawaan kedua variabel itu sudah mengarah ke API Monev resmi. Ubah kedua nilai itu hanya jika alamat API berubah.

Semua nilai di atas dapat Anda ubah sesuai kebutuhan. Contoh isi `.env` dengan nilai bawaan:

```
SIAPKERJA_USERNAME=your_nik_or_email_or_phone
SIAPKERJA_PASSWORD=your_password
CLOCK_IN_TIME=16:00
HARI_LIBUR=Sabtu,Minggu
LATITUDE=-6.2088
LONGITUDE=106.8456
LOCATION=Jakarta
ACTIVITY_LOG=Menjalankan kegiatan magang hari ini dengan mengikuti arahan mentor dan menyelesaikan aktivitas yang berkaitan dengan tugas serta kebutuhan proyek yang sedang dikerjakan.
LESSON_LEARNED=Memperoleh pengalaman dan pemahaman baru dari kegiatan magang hari ini, terutama terkait proses kerja, koordinasi, serta penerapan pengetahuan dalam penyelesaian tugas proyek.
OBSTACLES=Tidak terdapat kendala berarti selama kegiatan magang hari ini. Aktivitas dapat dilaksanakan dengan baik sesuai arahan mentor dan kebutuhan pekerjaan yang sedang dilakukan.
# Opsional: notifikasi Telegram
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```


### Penggunaan

Kirim absen masuk (status `PRESENT`) untuk hari ini:

```
python main.py absen
```

Tampilkan log absen hari ini:

```
python main.py status
```

Bila menggunakan uv, jalankan `uv run main.py absen` atau `uv run main.py status`. Perintah itu langsung menggunakan lingkungan `.venv` tanpa aktivasi.

Periksa kelayakan setup (variabel, login, Telegram, scheduler):

```
python main.py doctor
```

Tampilkan payload absen tanpa mengirim:

```
python main.py absen --dry-run
```

Tampilkan absen 7 hari terakhir:

```
python main.py status --days 7
```

Setiap run mencatat hasilnya ke `absen.log` di folder proyek, lengkap dengan stempel waktu.

Program mengirim data berikut ke `POST /attendances/with-daily-log`:

```json
{
  "date": "2026-09-21",
  "status": "PRESENT",
  "activity_log": "...",
  "lesson_learned": "...",
  "obstacles": "..."
}
```

Contoh keluaran perintah `status`:

```
Status: 2026-09-21
  Aktivitas:  Menjalankan kegiatan magang hari ini.
  Pelajaran:  Memperoleh pengalaman baru.
  Kendala:    Tidak ada kendala.
```

## Penjadwalan Otomatis

### Task Scheduler (Windows)

Skrip `setup_task.ps1` membuat tugas Windows Task Scheduler bernama `AutoAbsenMaganghub`. Tugas itu menjalankan `python main.py absen` setiap hari pada jam yang Anda tentukan. Skrip menggunakan Python dari `.venv` bila ada. Bila tidak ada, skrip menggunakan Python dari PATH.

Catatan soal jadwal ini:

- Laptop boleh tidur. Pada jam absen, tugas mengaktifkan kembali laptop yang tidur, asalkan laptop sedang tercolok ke pengisi daya.
- Bila laptop mati total atau tidak tercolok, tugas menunggu sampai laptop menyala lagi, lalu absen terkirim saat itu juga.

1. Isi `CLOCK_IN_TIME` di `.env` dengan format `HH:MM`. Skrip menggunakan nilai itu sebagai jam tugas. Bila kosong, skrip menggunakan `16:00`.
2. Buka PowerShell sebagai Administrator (klik kanan > Run as Administrator), lalu jalankan skrip. Tanpa Administrator, pendaftaran tugas gagal:

   ```
   powershell -ExecutionPolicy Bypass -File .\setup_task.ps1
   ```

Untuk mematikan otomatisasi, hapus tugas:

```
Unregister-ScheduledTask -TaskName 'AutoAbsenMaganghub' -Confirm:$false
```

Untuk memeriksa status tugas:

```
Get-ScheduledTask -TaskName 'AutoAbsenMaganghub'
```

### GitHub Actions

Berkas `.github/workflows/absen.yml` menjalankan `python main.py absen` setiap hari pukul 16:00 WIB. Jadwal ditulis dalam UTC: `0 9 * * *`.

1. Unggah proyek ini ke repositori GitHub.
2. Buka Settings > Secrets and variables > Actions > New repository secret. Buat secret berikut:
   - `SIAPKERJA_USERNAME`
   - `SIAPKERJA_PASSWORD`
   - `ACTIVITY_LOG`
   - `LESSON_LEARNED`
   - `OBSTACLES`
   - `TELEGRAM_BOT_TOKEN` (opsional, untuk notifikasi)
   - `TELEGRAM_CHAT_ID` (opsional, untuk notifikasi)
3. Jalankan manual sekali lewat Actions > Absen > Run workflow untuk memastikan semuanya bekerja.

Untuk mematikan otomatisasi, buka Actions > Absen > tombol `...` > Disable workflow. Untuk menyalakan lagi, pilih Enable workflow di tempat yang sama.

Empat hal yang perlu Anda ketahui:

- GitHub tidak menjamin cron berjalan tepat waktu.
- Request berjalan dari server GitHub di luar Indonesia, sementara data lokasi absen mengklaim Jakarta.
- Jam eksekusi dikunci di baris cron berkas workflow. `CLOCK_IN_TIME` tidak berpengaruh pada jadwal GitHub Actions. Ubah baris cron untuk mengganti jam.
- Pada hari libur (`HARI_LIBUR`), program berhenti sendiri tanpa mengirim absen. Program tidak mengirim notifikasi pada hari itu.

## Notifikasi Telegram

Program mengirim pesan Telegram setiap kali absen berhasil atau gagal. Notifikasi tidak aktif bila `TELEGRAM_BOT_TOKEN` atau `TELEGRAM_CHAT_ID` kosong.

Cara mendapatkan keduanya:

1. Chat `@BotFather` di Telegram, kirim `/newbot`, lalu ikuti balasannya. BotFather memberi token bot.
2. Kirim satu pesan apa pun ke bot yang baru dibuat.
3. Buka `https://api.telegram.org/bot<TOKEN_KAMU>/getUpdates` di peramban. Cari `"chat":{"id":...}` pada JSON yang tampil. Angka itu adalah chat ID.
4. Isi kedua variabel di `.env` (jadwal lokal) atau di GitHub Secrets (GitHub Actions).

## Informasi Proyek

### Struktur Proyek

```
auto-absen-maganghub/
├── main.py                   titik masuk CLI (absen, status, doctor)
├── app/
│   ├── commands.py           perintah absen, status, doctor, dry-run
│   ├── config.py             konfigurasi dari .env
│   ├── auth/
│   │   └── sso.py            login SSO Kemnaker dan access token
│   ├── api/
│   │   └── client.py         klien HTTP API Monev
│   ├── models/
│   │   └── attendance.py     logika absen dan pembacaan log
│   └── utils/
│       ├── log.py            console dan berkas absen.log
│       ├── net.py            error jaringan dan retry
│       ├── telegram.py       notifikasi Telegram
│       └── time.py           waktu zona WIB
├── tests/
│   └── test_main.py          tes otomatis (pytest)
├── .github/
│   └── workflows/
│       ├── absen.yml         penjadwalan GitHub Actions
│       └── tests.yml         tes tiap push
├── setup_task.ps1            tugas Windows Task Scheduler
├── .env.example              contoh berkas .env
├── requirements.txt          dependensi Python
├── requirements-dev.txt      dependensi pengembangan
├── LICENSE                   lisensi MIT
└── .gitattributes            akhir baris Git
```

### Keamanan

- Berkas `.env` memuat kata sandi akun Anda. Jangan mengunggah berkas itu ke repositori publik.
- Jangan membagikan isi berkas `.env` kepada siapa pun.
- Untuk GitHub Actions, simpan kredensial sebagai Secrets. Jangan menulis kredensial di berkas workflow.

### Peringatan

Penulis menyediakan program ini "sebagaimana adanya", tanpa jaminan apa pun. Gunakan program ini dengan risiko sendiri ("use at your own risk").

Program mengotomatiskan pengiriman absen. Program ini dirancang sebagai pengaman saat lupa absen, bukan sebagai pengganti absen manual. Pastikan cara pakai ini sesuai dengan aturan di tempat magang Anda.

Penulis tidak bertanggung jawab atas akibat apa pun dari penggunaan program ini. Akibat itu mencakup penangguhan akun, sanksi, atau kerugian lain.

### Kontribusi

Kontribusi berupa issue dan pull request terbuka untuk siapa pun.

1. Fork repositori ini, lalu buat branch untuk perubahan Anda.
2. Jangan commit berkas `.env` ke repositori.
3. Pasang dependensi pengembangan, lalu pastikan tes lolos sebelum membuka pull request:

   ```
   pip install -r requirements-dev.txt
   python -m pytest
   ```

4. Buka pull request dengan penjelasan singkat tentang perubahan Anda.

### Atribusi

Gaya bahasa Indonesia di README ini mengikuti [indonesian-writing-skills](https://github.com/pataanggs/indonesian-writing-skills) oleh pataanggs.

### Lisensi

Proyek ini berlisensi MIT. Lihat berkas `LICENSE` untuk teks lengkapnya.
