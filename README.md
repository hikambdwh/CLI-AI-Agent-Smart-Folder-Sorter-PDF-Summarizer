# CLI-AI-Agent-Smart-Folder-Sorter-PDF-Summarizer

# AI File Organizer & PDF Summarizer (OpenRouter) — CLI Agent

Aplikasi **CLI berbasis Python** untuk membantu merapikan file tugas secara otomatis dan merangkum dokumen PDF menggunakan LLM melalui **OpenRouter API**.

## Fitur
- **Smart Folder Sorter**
  - Mengelompokkan & memindahkan file ke subfolder berdasarkan ekstensi:
    - `word/` → `.docx .doc .rtf`
    - `worksheet/` → `.xlsx .xls .csv`
    - `pdf/` → `.pdf`
    - `image/` → `.jpg .jpeg .png .gif`
  - Aman terhadap nama file bentrok (auto tambah suffix: `file (1).pdf`, dst).

- **PDF Summarizer**
  - Mengekstrak teks dari PDF (PyPDF2), lalu menghasilkan:
    1) Ringkasan singkat (2–3 kalimat)  
    2) Ringkasan lengkap (1 paragraf)  
    3) 5 poin penting  

- **Interactive CLI**
  - Input perintah via terminal + output berwarna (Colorama).

## Tech Stack
Python, Requests, PyPDF2, Colorama, python-dotenv, OpenRouter API

---

## Struktur Proyek (contoh)
