# Project 01: AI Commit Changelog Generator

This project builds a small DevOps utility that turns the latest git diff into a clean, human-ready commit message and a short changelog entry. It is designed for teams who want consistent commit history and fast release notes without relying on cloud AI services.

## How It Works
1. Pull the diff between `HEAD~1` and `HEAD`.
2. Truncate the diff to a safe size.
3. Send the diff to a local Ollama model.
4. Print a conventional commit message and a markdown changelog snippet.

## Prerequisites
- Git
- Python 3
- Ollama running locally with the `llama3` model

## Usage
1. Start Ollama locally:
   ```bash
   ollama serve
   ```
2. Pull the model if needed:
   ```bash
   ollama pull llama3
   ```
3. From the project directory, run:
   ```bash
   pip install requests
   ```
4. Run the script:
   ```bash
   python scripts/generate_changelog.py
   ```

Optional configuration via `.env.example`:
- `OLLAMA_HOST` (default `http://localhost:11434`)
- `MODEL_NAME` (default `llama3`)

## Sample Output
```
-------------------------
Commit Message:
feat: add validation for missing git history

Changelog:
- Added safe handling for repos without prior commits.
- Improved errors when git is not installed.
-------------------------
```

## YouTube
🎥 Part of the ThinkWithOps DevOps + AI Project Series
