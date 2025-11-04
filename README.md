# F.R.A.N.C.I.S-
Facilitating Residential Assistance, Navigation, and Comfort with Intelligent Systems (F.R.A.N.C.I.S) is an AI Home Assistant inspired by Tony Stark's "J.A.R.V.I.S" from the MCU. The project aims to create an intelligent, context-aware assistant capable of natural interaction and task automation.

![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)

## Features & Goals

### Current Features
- Natural language interaction using Qwen3 8B LLM
- Project-aware coding assistance
- Context-aware responses
- File system integration

### Planned Features
- Voice interaction and recognition
- Smart home device integration
- Task automation and scheduling
- Personal memory and learning
- Advanced coding assistance with:
  - Code generation
  - Debugging help
  - Project management
  - Documentation generation

## Project Structure
```
F.R.A.N.C.I.S/
├── src/            # Source code
│   └── main.py     # Main assistant interface
├── config/         # Configuration files
└── docs/           # Documentation
```

## Setup

### Prerequisites
1. Python 3.14 or higher
2. [Ollama](https://ollama.ai/) installed
3. Qwen3 8B model

### Installation
1. Clone the repository:
	```bash
	git clone https://github.com/ayden-rebhan/F.R.A.N.C.I.S.git
	cd F.R.A.N.C.I.S
	```

2. Start Ollama server:
	```bash
	ollama serve
	```

3. Pull the Qwen3 model:
	```bash
	ollama pull qwen3:8b
	```

4. Run F.R.A.N.C.I.S:
	```bash
	python src/main.py
	```

## Usage

### Basic Interaction
- Start a conversation with natural language input
- Ask questions or request assistance
- Type 'exit' to quit

### Coding Assistance
F.R.A.N.C.I.S can help with:
- Code analysis and review
- Project structure understanding
- File management
- Development suggestions
- Day-to-day automation

### Examples
```
You: What files are in this project?
You: Help me understand the main.py file
You: Suggest improvements for error handling
```

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for:
- New features
- Bug fixes
- Documentation improvements
- Feature requests

## License

This project is licensed under the **Apache License 2.0** — see the [LICENSE](./LICENSE) file for details.

You are free to use, modify, and distribute this software for personal or commercial purposes, provided that proper attribution is given and any significant modifications are documented.