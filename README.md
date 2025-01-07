# snaprepo 📋
Stop copy-pasting code manually into AI. `snaprepo` automates sharing your codebase with AI tools by formatting it for readability and handling clipboard operations automatically.

## Features

- **Direct to Clipboard**: Run `snaprepo` to format your project and copy it to the clipboard instantly.
- **Auto-Format**: Generate clean Markdown with proper syntax highlighting for 25+ languages.
- **Smart Filtering**: Automatically excludes binaries, large files, and irrelevant content using `.gitignore`.
- **Token Aware**: Get instant token usage estimates for GPT-4, Claude, and other models.
- **Security First**: Automatically redacts sensitive files and configuration data.
- **Template Support**: Preserves template files (`*.example`, `*.sample`) with proper formatting.
- **Flexible Output**: Stream to clipboard, save to file, or pipe to other tools.
- **Fast & Reliable**: Built in Python with minimal dependencies.

## Quick Start

```bash
# Install from source (see Installation section)
git clone https://github.com/scharc/snaprepo.git
cd snaprepo
make install-user

# Copy entire project to clipboard (default command)
cd your-project
snaprepo

# Or save to file
snaprepo snap

# Get token usage stats
snaprepo tokens
```

## Installation

### Prerequisites
- Python 3.8+
- Poetry (optional, for development)

### Install Methods

From source:
```bash
git clone https://github.com/scharc/snaprepo.git
cd snaprepo
make install-user  # Install for current user
# OR
make install-system  # System-wide installation (sudo)
```

## Usage

### 1. Direct to Clipboard (Default)
Just run `snaprepo` in your project directory to automatically format and copy to clipboard:
```bash
cd your-project
snaprepo
```

Options:
- `-p, --path PATH`: Path to the project directory (default: current directory).
- `--max-file-size BYTES`: Maximum file size to include (default: 1MB).
- `--skip-common`: Skip commonly referenced files like `LICENSE` and `README`.
- `--skip-files PATTERN`: Additional patterns to skip (e.g., `*.log`).

### 2. Save to File
Generate a Markdown snapshot file:
```bash
snaprepo snap [options]
```

Options:
- `-p, --path PATH`: Path to the project directory (default: current directory).
- `-o, --output FILE`: Output file (default: `{project}_source.md`).
- `--max-file-size BYTES`: Maximum file size to include (default: 1MB).
- `--skip-common`: Skip commonly referenced files like `LICENSE` and `README`.
- `--skip-files PATTERN`: Additional patterns to skip (e.g., `*.log`).
- `--summary/--no-summary`: Show or hide project stats (default: `--summary`).
- `-f, --force`: Overwrite the output file if it exists.

### 3. Stream to Clipboard Manually
Use the `stream` command with your preferred clipboard tool:
```bash
# macOS
snaprepo stream | pbcopy

# Linux (X11)
snaprepo stream | xclip -selection clipboard
# or
snaprepo stream | xsel --clipboard

# Linux (Wayland)
snaprepo stream | wl-copy

# Windows (PowerShell)
snaprepo stream | Set-Clipboard
```

Options:
- `-p, --path PATH`: Path to the project directory (default: current directory).
- `--max-file-size BYTES`: Maximum file size to include (default: 1MB).
- `--skip-common`: Skip commonly referenced files like `LICENSE` and `README`.
- `--skip-files PATTERN`: Additional patterns to skip (e.g., `*.log`).

### 4. Token Analysis
Check token usage across different AI models:
```bash
snaprepo tokens [FILE]  # FILE is optional
```

Example output:
```
Project File Statistics
  • File Name: myproject_source.md
  • Characters: 12,345
  • Lines: 234
  • Code Blocks: 3

Model-Specific Token Estimates:
  • GPT-4: 1,234 tokens
     ↳ Max Context: 8,192  |  Usage: 15.1%  |  Remaining: 6,958
  • Claude: 987 tokens
     ↳ Max Context: 100,000  |  Usage: 0.9%  |  Remaining: 99,013
```

### Shell Completion

Add to your shell config:
```bash
# Bash (~/.bashrc)
source <(snaprepo completion bash)

# Zsh (~/.zshrc)
source <(snaprepo completion zsh)
```

## Security Features

`snaprepo` automatically redacts sensitive files and data:
- Environment files (`.env`).
- Configuration files (`*.yml`, `wp-config.php`).
- Credentials (API keys, tokens).
- SSH and encryption keys.
- Authentication files (`.htpasswd`).
- Other sensitive data patterns.

Template files (`*.example`, `*.sample`) are preserved but clearly marked.

## Development

```bash
# Setup
git clone https://github.com/scharc/snaprepo.git
cd snaprepo
poetry install

# Build and test
make build
make clean
make install-user
```

