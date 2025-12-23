import os
import shutil
from pathlib import Path
import requests
import PyPDF2
from colorama import init, Fore, Style

# Optional: pip install python-dotenv
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# Inisialisasi warna terminal
init(autoreset=True)


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")  # wajib di env/.env
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")

BASE_FOLDER = os.getenv("BASE_FOLDER", r"D:\Tugas Hikam")

MAX_PDF_CHARS = int(os.getenv("MAX_PDF_CHARS", "20000"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "60"))



def ensure_api_key():
    if not OPENROUTER_API_KEY:
        raise RuntimeError(
            "OPENROUTER_API_KEY belum diset. "
            "Set env var OPENROUTER_API_KEY atau buat file .env."
        )


def safe_move(src: Path, dst_dir: Path) -> Path:
    """
    Pindahkan file ke folder tujuan.
    Jika nama file sudah ada, tambahkan suffix (1), (2), dst.
    """
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / src.name

    if not dst.exists():
        shutil.move(str(src), str(dst))
        return dst

    stem, suffix = src.stem, src.suffix
    i = 1
    while True:
        candidate = dst_dir / f"{stem} ({i}){suffix}"
        if not candidate.exists():
            shutil.move(str(src), str(candidate))
            return candidate
        i += 1


def smart_folder_sorter(base_path=BASE_FOLDER):
    base_path = Path(base_path)

    mapping = {
        "word": [".docx", ".doc", ".rtf"],
        "worksheet": [".xlsx", ".xls", ".csv"],
        "pdf": [".pdf"],
        "image": [".jpg", ".jpeg", ".png", ".gif"],
    }

    results = {key: 0 for key in mapping.keys()}

    if not base_path.exists():
        raise FileNotFoundError(f"Folder tidak ditemukan: {base_path}")

    for item in base_path.iterdir():
        if not item.is_file():
            continue

        ext = item.suffix.lower()
        for folder, ext_list in mapping.items():
            if ext in ext_list:
                target_dir = base_path / folder
                safe_move(item, target_dir)
                results[folder] += 1
                break

    return results


def extract_text_from_pdf(pdf_path: str) -> str:
    """Mengambil seluruh text dari file PDF (best effort)."""
    text_parts = []
    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text_parts.append(extracted)
    return "\n".join(text_parts)


def summarize_pdf(llm_api, pdf_path: str) -> str:
    text = extract_text_from_pdf(pdf_path)

    # Hindari prompt kepanjangan
    if len(text) > MAX_PDF_CHARS:
        text = text[:MAX_PDF_CHARS] + "\n\n[TEKS DIPOTONG AGAR TIDAK TERLALU PANJANG]"

    summary_prompt = (
        "Tolong ringkas dokumen PDF berikut:\n\n"
        f"{text}\n\n"
        "Buatkan tiga bagian:\n"
        "1. Ringkasan singkat (2–3 kalimat).\n"
        "2. Ringkasan lengkap (1 paragraf).\n"
        "3. 5 poin-poin penting.\n"
        "Jawab dalam bahasa Indonesia."
    )

    llm_api.reset_messages_to_system()
    llm_api.add_message("user", summary_prompt)
    return llm_api.get_response()


class LLM_API:
    def __init__(self, model: str = OPENROUTER_MODEL):
        ensure_api_key()
        self.model = model
        self.headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",

            # Optional (direkomendasikan OpenRouter untuk metadata aplikasi)
            # "HTTP-Referer": "https://github.com/username/repo",
            # "X-Title": "AI File Organizer & PDF Summarizer",
        }
        self.system_prompt = None
        self.payload = {"model": self.model, "messages": [], "stream": False}

    def set_system_prompt(self, prompt: str):
        self.system_prompt = prompt
        self.payload["messages"] = [{"role": "system", "content": prompt}]

    def add_message(self, role: str, content: str):
        self.payload["messages"].append({"role": role, "content": content})

    def reset_messages_to_system(self):
        self.payload["messages"] = []
        if self.system_prompt:
            self.payload["messages"].append({"role": "system", "content": self.system_prompt})

    def get_response(self) -> str:
        try:
            response = requests.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                headers=self.headers,
                json=self.payload,
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except requests.RequestException as e:
            return f"[ERROR] Gagal memanggil OpenRouter: {e}"

    def start_chat(self, base_folder: str = BASE_FOLDER):
        base_folder = str(base_folder)

        print(Fore.CYAN + f"Base folder aktif: {base_folder}")
        print(Fore.CYAN + "Ketik 'q' untuk keluar.\n")

        while True:
            user_input = input(Fore.GREEN + "User: " + Style.RESET_ALL).strip()

            if user_input.lower() in ["exit", "quit", "q"]:
                print(Fore.CYAN + "Agent: Sampai jumpa!")
                break

            if any(k in user_input.lower() for k in ["rapihkan", "sortir", "pindahkan"]):
                print(Fore.YELLOW + "[AI THINKING] Menjalankan perintah sortir..." + Style.RESET_ALL)

                try:
                    result = smart_folder_sorter(base_folder)
                except Exception as e:
                    print(Fore.CYAN + f"[TOOL OUTPUT] Gagal sortir: {e}")
                    continue

                print(Fore.CYAN + f"[TOOL OUTPUT] Hasil pemindahan file: {result}")

                self.reset_messages_to_system()
                self.add_message("user", f"Tolong jelaskan hasil pemindahan file berikut kepada user: {result}")
                ai_answer = self.get_response()
                print(Fore.CYAN + ai_answer)
                continue

            if ("ringkas" in user_input.lower() or "rangkum" in user_input.lower()) and ".pdf" in user_input.lower():
                filename = user_input.split()[-1]
                pdf_path = Path(base_folder) / "pdf" / filename

                if not pdf_path.exists():
                    print(Fore.CYAN + f"[TOOL OUTPUT] File PDF tidak ditemukan: {pdf_path}")
                    continue

                print(Fore.YELLOW + "[AI THINKING] Membaca dan merangkum PDF..." + Style.RESET_ALL)
                summary = summarize_pdf(self, str(pdf_path))
                print(Fore.CYAN + "[TOOL OUTPUT] Ringkasan PDF selesai dibuat:\n")
                print(Fore.CYAN + summary)
                continue

            self.reset_messages_to_system()
            self.add_message("user", user_input)

            print(Fore.YELLOW + "[AI THINKING] Memproses..." + Style.RESET_ALL)
            ai_answer = self.get_response()
            print(Fore.CYAN + "Agent: " + ai_answer)


if __name__ == "__main__":
    llm_api = LLM_API()
    llm_api.set_system_prompt(
        "Kamu adalah AI Agent untuk membantu Hikam menjawab dan menyelesaikan segala masalahnya. "
        "Gunakan bahasa Indonesia yang jelas."
    )
    llm_api.start_chat(BASE_FOLDER)
