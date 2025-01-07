# snaprepo/config.py

# Files and directories that should be shown as redacted
REDACTED_PATTERNS = {
    ".env": "[REDACTED - Environment Variables]",
    "development.yml": "[REDACTED - Development Config]",
    "production.yml": "[REDACTED - Production Config]",
    "staging.yml": "[REDACTED - Staging Config]",
    "secrets/": "[REDACTED - Directory containing sensitive data]",
    ".aws/": "[REDACTED - AWS Configuration]",
    ".ssh/": "[REDACTED - SSH Keys and Configuration]",
    "id_rsa": "[REDACTED - SSH Private Key]",
    "id_rsa.pub": "[REDACTED - SSH Public Key]",
    ".htpasswd": "[REDACTED - HTTP Basic Auth Passwords]",
    "wp-config.php": "[REDACTED - WordPress Configuration]",
    "config/secrets.yml": "[REDACTED - Application Secrets]",
    "credentials.json": "[REDACTED - API Credentials]",
    ".npmrc": "[REDACTED - NPM Configuration]",
    ".pypirc": "[REDACTED - PyPI Configuration]",
}

# Patterns for files that might contain sensitive data
SENSITIVE_PATTERNS = {
    "**/id_rsa",
    "**/id_dsa",
    "**/*.pem",
    "**/*.key",
    "**/*.p12",
    "**/*.pfx",
    "**/authorized_keys",
    "**/known_hosts",
    "**/oauth_token",
    "**/oauth.json",
    "**/credentials.json",
    "**/.netrc",
}

# Common files to skip
COMMON_FILES = {
    "LICENSE",
    "LICENSE.md",
    "LICENSE.txt",
    "CONTRIBUTING.md",
    "CONTRIBUTING",
    "CODE_OF_CONDUCT.md",
    "CODE_OF_CONDUCT",
    "CHANGELOG.md",
    "CHANGELOG",
    "SECURITY.md",
    "SECURITY",
    ".gitattributes",
    ".editorconfig",
    ".dockerignore",
}

# Common binary extensions to ignore
BINARY_EXTENSIONS = {
    # Images
    "png", "jpg", "jpeg", "gif", "bmp", "tiff", "webp", "ico", "svg", "psd", 
    "ai", "eps", "raw",
    # Documents and archives
    "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "zip", "tar", "gz", 
    "rar", "7z", "bz2", "iso",
    # Executables and libraries
    "exe", "dll", "so", "dylib", "lib", "obj", "bin", "apk", "app", "msi",
    # Fonts
    "ttf", "otf", "woff", "woff2", "eot",
    # Media
    "mp3", "mp4", "wav", "ogg", "avi", "mov", "wmv", "flv", "mkv", "aac", 
    "m4a", "flac",
    # Database
    "db", "sqlite", "sqlite3", "mdb", "frm", "ibd",
    # Other binary formats
    "class", "pyc", "pyo", "pyd", "o", "a", "pkl", "dat",
}

# Language identifier mapping
EXTENSION_MAP = {
    "js": "javascript",
    "jsx": "javascript",
    "ts": "typescript",
    "tsx": "typescript",
    "py": "python",
    "rb": "ruby",
    "java": "java",
    "cpp": "cpp",
    "c": "c",
    "cs": "csharp",
    "php": "php",
    "go": "go",
    "rs": "rust",
    "swift": "swift",
    "kt": "kotlin",
    "r": "r",
    "sql": "sql",
    "yaml": "yaml",
    "yml": "yaml",
    "json": "json",
    "md": "markdown",
    "html": "html",
    "css": "css",
    "scss": "scss",
    "less": "less",
    "sh": "bash",
    "bash": "bash",
    "dockerfile": "dockerfile",
}

# Default ignore patterns
DEFAULT_IGNORE_PATTERNS = [
    # Version Control
    ".git/",
    "node_modules/",
    "dist/",
    "build/",
    "coverage/",
    ".DS_Store",
    "*.log",
    "*.lock",
    "package-lock.json",
    "__pycache__/",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    ".Python",
    "env/",
    "venv/",
    ".venv/",
    "ENV/",
    "env.bak/",
    "venv.bak/",
]

# Template file suffixes
TEMPLATE_SUFFIXES = (
    ".example",
    ".sample",
    ".template",
    ".dist",
    "example.yml",
    "sample.yml",
    ".example.json",
    ".sample.json",
    ".template.yaml",
    ".template.yml",
)

# Add to config.py

MODEL_SPECS = {
    "GPT-4": {
        "multiplier": 1.00,
        "max_context": 8192,
    },
    "GPT-3.5": {
        "multiplier": 1.00,
        "max_context": 4096,
    },
    "Claude": {
        "multiplier": 0.80,
        "max_context": 100000,
    },
    "GPT-O1": {
        "multiplier": 1.10,
        "max_context": 4096,
    },
    "Ollama-Llama2-7B": {
        "multiplier": 0.90,
        "max_context": 4096,
    },
    "Ollama-Llama2-13B": {
        "multiplier": 0.85,
        "max_context": 4096,
    },
}

# Add to config.py
DEFAULT_STATS = {
    "total_files": 0,
    "included_files": 0,
    "binary_files": 0,
    "ignored_files": 0,
    "total_size": 0,
    "languages": set(),
}