"""Константы проекта Code Bundler.
Все настраиваемые значения (метки, лимиты, расширения) — здесь."""

# --- Шаблоны меток файлов (ЗАФИКСИРОВАНЫ) ---
FILE_START_TEMPLATE = "// ===== FILE START: {path} ====="
FILE_END_TEMPLATE = "// ===== FILE END: {path} ====="

# --- Расширения по языкам ---
CPP_EXTENSIONS = {".cpp", ".cc", ".cxx", ".c", ".h", ".hpp", ".hxx", ".hh"}
PYTHON_EXTENSIONS = {".py", ".pyw"}

# Все поддерживаемые расширения кода
CODE_EXTENSIONS = CPP_EXTENSIONS | PYTHON_EXTENSIONS

# --- Игнорируемые папки/файлы по умолчанию ---
DEFAULT_IGNORE = {
    "build", "cmake-build-debug", "cmake-build-release",
    ".git", ".svn", ".hg",
    ".vs", ".vscode", ".idea",
    "__pycache__", ".pytest_cache",
    "venv", ".venv", "env",
    "node_modules", "dist", "out",
}

# --- Токены ---
DEFAULT_TOKEN_LIMIT = 120_000
DEFAULT_TIKTOKEN_MODEL = "cl100k_base"
# Грубая оценка, если tiktoken недоступен: символов на 1 токен
FALLBACK_CHARS_PER_TOKEN = 4

# --- Кодировки для чтения файлов (пробуем по порядку) ---
FILE_ENCODINGS = ("utf-8", "utf-8-sig", "cp1251", "latin-1")