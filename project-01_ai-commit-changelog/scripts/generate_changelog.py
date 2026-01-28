#!/usr/bin/env python3
"""
AI Commit & Changelog Generator (Local Version)
Uses Ollama (llama3, codellama, etc.) to generate:
- A conventional commit message (<72 chars)
- A user-friendly changelog snippet (2-3 bullet points)

Designed to run locally where Ollama is installed and running.
"""

import os
import sys
import subprocess
import requests
import json
from datetime import date
from typing import Optional, Tuple
from dotenv import load_dotenv

load_dotenv()  # ← This loads .env automatically

# Configuration
MAX_DIFF_CHARS = int(os.getenv("MAX_DIFF_CHARS", "400"))  # Faster default
DEFAULT_OLLAMA_HOST = "http://localhost:11434"
DEFAULT_MODEL_NAME = "phi3"
DEFAULT_RELEASE_VERSION = "v1.0"


def get_git_diff() -> Tuple[Optional[str], Optional[str]]:
    """Get diff of the last commit (HEAD vs HEAD~1) using UTF-8 encoding."""
    try:
        # Force UTF-8 to handle emojis, special chars, etc.
        result = subprocess.run(
            ["git", "diff", "--cached"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            encoding='utf-8',          # Critical: force UTF-8
            errors='replace'           # Replace undecodable chars instead of crashing
        )
    except FileNotFoundError:
        return None, "❌ Git not found. Is Git installed and in PATH?"
    except Exception as e:
        return None, f"❌ Failed to run git: {e}"

    if result.returncode != 0:
        err = result.stderr.strip().lower()
        if "not a git repository" in err:
            return None, "❌ Not a Git repository."
        if "unknown revision" in err or "bad revision" in err:
            return None, "❌ Need at least one prior commit (push after first commit)."
        return None, f"❌ Git error: {result.stderr.strip()}"

    diff = result.stdout.strip()
    if not diff:
        return None, "ℹ️ No changes detected in the last commit."

    return diff[:MAX_DIFF_CHARS], None


def build_prompt(diff: str) -> str:
    return f"""You are a senior DevOps engineer. Your job is to write a concise git commit message and a changelog.

RULES:
- First line MUST be a conventional commit: type(scope): description
- Then write a changelog with 2-3 bullet points starting with "- "
- NO extra text, NO explanations, NO markdown headers

Example:
feat(auth): add password reset flow
- Add 'Forgot Password' button on login page
- Implement email token validation

Now analyze this diff:

{diff}"""


def call_ollama(prompt: str, host: str, model: str) -> Tuple[Optional[str], Optional[str]]:
    """Call Ollama with optimized settings for speed and brevity."""
    url = f"{host.rstrip('/')}/api/chat"

    # Get optional config from env
    max_tokens = int(os.getenv("OLLAMA_MAX_TOKENS", "80"))  # Cap output
    keep_alive = os.getenv("OLLAMA_KEEP_ALIVE", "15m")       # Keep model loaded

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {
            "temperature": 0.3,
            "num_predict": max_tokens,          # Stop after N tokens
            "stop": ["\n\n", "COMMIT_MESSAGE"]  # Stop early if pattern seen
        },
        "keep_alive": keep_alive                # Keep in memory
    }

    try:
        resp = requests.post(url, json=payload, timeout=60)
    except requests.RequestException as e:
        return None, f"❌ Failed to connect to Ollama at {url}: {e}"

    if resp.status_code != 200:
        return None, f"❌ Ollama error ({resp.status_code}): {resp.text[:200]}"

    try:
        content = resp.json()["message"]["content"]
        return content.strip(), None
    except (KeyError, json.JSONDecodeError):
        return None, "❌ Unexpected response format from Ollama."


def parse_ai_response(response: str) -> Tuple[str, str]:
    """Extract commit message and changelog from AI output (flexible parsing)."""
    lines = response.splitlines()

    # Strategy 1: Try to find a line that looks like a conventional commit
    commit_msg = None
    changelog_lines = []

    # Look for a line that starts with type(scope): or type:
    import re
    commit_pattern = re.compile(r'^[a-z]+(\([^)]+\))?:\s*.{5,}$')

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # If line matches conventional commit format, use it
        if commit_pattern.match(line):
            commit_msg = line
            break

    # If no structured commit found, try first short line (<80 chars, not bullet)
    if not commit_msg:
        for line in lines:
            line = line.strip()
            if line and not line.startswith(('-', '*', '•', '#', 'CHANGELOG', 'Commit')):
                # Avoid obvious non-commit lines
                if 'commit' not in line.lower() and 'message' not in line.lower():
                    commit_msg = line
                    break

    # Fallback
    if not commit_msg:
        commit_msg = "chore: update changes"

    # Extract changelog: look for bullet points
    in_changelog = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(('CHANGELOG', 'Changelog', '###')):
            in_changelog = True
            continue
        if in_changelog and stripped.startswith(('-', '*', '•')):
            changelog_lines.append(stripped)
        elif in_changelog and not stripped:
            # End of changelog section
            break

    # If no bullets found, scan entire response for bullets
    if not changelog_lines:
        for line in lines:
            stripped = line.strip()
            if stripped.startswith(('-', '*', '•')):
                changelog_lines.append(stripped)

    if not changelog_lines:
        changelog_lines = ["- Minor updates."]

    changelog = "\n".join(changelog_lines)
    return commit_msg, changelog


def main():
    print("🔍 Analyzing your latest commit with AI...\n")

    diff, error = get_git_diff()
    if error:
        print(error)
        if "Need at least one prior commit" in error:
            print("\n💡 Tip: Make your first commit, then run this after the second.")
        sys.exit(1 if "❌" in error else 0)
    print("INFO Using staged changes (git diff --cached).")

    # Load config
    ollama_host = os.getenv("OLLAMA_HOST", DEFAULT_OLLAMA_HOST)
    model_name = os.getenv("MODEL_NAME", DEFAULT_MODEL_NAME)

    print(f"🧠 Using model: {model_name} @ {ollama_host}")
    print("⏳ This may take 10-30 seconds (first run loads model)...\n")

    prompt = build_prompt(diff)
    response, error = call_ollama(prompt, ollama_host, model_name)
    if error:
        print(error)
        sys.exit(1)

    commit_msg, changelog = parse_ai_response(response)

    # Output
    release_version = os.getenv("RELEASE_VERSION", DEFAULT_RELEASE_VERSION)
    print("=" * 60)
    print("✅ AI-Generated Commit Message:")
    print(f"\033[1m{commit_msg}\033[0m\n")
    print("📝 Changelog Snippet:")
    print(f"### Unreleased ({release_version}) — {date.today().isoformat()}")
    print(changelog)
    print("=" * 60)
    print("\n💡 Copy the commit message above and use:\n")
    print("# If you already committed:")
    print(f'git commit --amend -m "{commit_msg}"')
    print("\n# Or for a new commit:")
    print(f'git commit -m "{commit_msg}"')


if __name__ == "__main__":
    main()
