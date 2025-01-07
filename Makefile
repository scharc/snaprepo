.PHONY: install clean build all dist completions install-system uninstall

# Default Python interpreter and package manager
PYTHON = python3
POETRY = poetry

# Output binary name
BINARY_NAME = snaprepo

# Operating system detection
ifeq ($(OS),Windows_NT)
	BINARY_SUFFIX = .exe
else
	BINARY_SUFFIX =
endif

# Installation directory detection
ifeq ($(shell uname),Darwin)  # macOS
	INSTALL_DIR = /usr/local/bin
	COMPLETION_DIR = /usr/local/share/zsh/site-functions
else  # Linux
	INSTALL_DIR = /usr/local/bin
	COMPLETION_DIR = /etc/bash_completion.d
endif

install:
	$(POETRY) install

clean:
	rm -rf dist/
	rm -rf build/
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".DS_Store" -delete

build: clean install
	# Ensure we use poetry's environment
	$(POETRY) run pip install -U pyinstaller
	$(POETRY) run pyinstaller snaprepo.spec --clean

dist: build

# Install completions for the current user
completions-user:
	@echo "Installing shell completions for current user..."
	@mkdir -p ~/.local/share/bash-completion/completions
	@cp completions/$(BINARY_NAME).bash ~/.local/share/bash-completion/completions/$(BINARY_NAME)
ifeq ($(shell uname),Darwin)
	@mkdir -p ~/.zsh/completions
	@cp completions/$(BINARY_NAME).zsh ~/.zsh/completions/_$(BINARY_NAME)
else
	@mkdir -p ~/.local/share/zsh/site-functions
	@cp completions/$(BINARY_NAME).zsh ~/.local/share/zsh/site-functions/_$(BINARY_NAME)
endif
	@echo "Shell completions installed for current user. You may need to restart your shell."

# Install the binary for the current user
install-user: dist
	@echo "Installing $(BINARY_NAME) for current user..."
	@mkdir -p ~/.local/bin
	@cp dist/$(BINARY_NAME)$(BINARY_SUFFIX) ~/.local/bin/$(BINARY_NAME)
	@chmod +x ~/.local/bin/$(BINARY_NAME)
	@echo "Installation complete. Make sure ~/.local/bin is in your PATH"
	@echo "Run '$(BINARY_NAME) --help' to get started."

# Install system-wide (requires sudo)
install-system: dist completions-generate
	@echo "Installing $(BINARY_NAME) system-wide (requires sudo)..."
	@echo "You might be asked for your sudo password."
	@sudo cp dist/$(BINARY_NAME)$(BINARY_SUFFIX) $(INSTALL_DIR)/$(BINARY_NAME)
	@sudo chmod 755 $(INSTALL_DIR)/$(BINARY_NAME)
	@sudo mkdir -p $(COMPLETION_DIR)
	@sudo cp completions/$(BINARY_NAME).bash $(COMPLETION_DIR)/$(BINARY_NAME)
ifeq ($(shell uname),Darwin)
	@sudo cp completions/$(BINARY_NAME).zsh $(COMPLETION_DIR)/_$(BINARY_NAME)
endif
	@echo "Installation complete. Run '$(BINARY_NAME) --help' to get started."

# Uninstall system-wide (requires sudo)
uninstall-system:
	@echo "Uninstalling $(BINARY_NAME) system-wide (requires sudo)..."
	@sudo rm -f $(INSTALL_DIR)/$(BINARY_NAME)
	@sudo rm -f $(COMPLETION_DIR)/$(BINARY_NAME)
	@sudo rm -f $(COMPLETION_DIR)/_$(BINARY_NAME)
	@echo "System-wide uninstallation complete."

# Uninstall user installation
uninstall-user:
	@echo "Uninstalling $(BINARY_NAME) from user directories..."
	@rm -f ~/.local/bin/$(BINARY_NAME)
	@rm -f ~/.local/share/bash-completion/completions/$(BINARY_NAME)
	@rm -f ~/.local/share/zsh/site-functions/_$(BINARY_NAME)
	@rm -f ~/.zsh/completions/_$(BINARY_NAME)
	@echo "User installation uninstalled."

# Default target
all: install build completions-generate
