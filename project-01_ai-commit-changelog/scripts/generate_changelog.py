import json
import os
import subprocess
import sys
from datetime import date
from typing import Optional, Tuple

import requests


MAX_DIFF_CHARS = 2000
DEFAULT_VERSION = "v1.0"
DEFAULT_OLLAMA_HOST = "http://localhost:11434"
DEFAULT_MODEL_NAME = "llama3"


def run_git_diff() -> Tuple[Optional[str], Optional[str]]:
    try:
        result = subprocess.run(
            ["git", "diff", "HEAD~1", "HEAD"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except FileNotFoundError:
        return None, "git is not installed or not in PATH."
    except Exception as exc:
        return None, f"failed to run git: {exc}"

    if result.returncode != 0:
        stderr = result.stderr.strip()
        if "not a git repository" in stderr.lower():
            return None, "this directory is not a git repository."
        if "bad revision" in stderr.lower() or "unknown revision" in stderr.lower():
            return None, "no previous commit found (need at least two commits)."
        return None, f"git diff failed: {stderr or 'unknown error'}"

    diff_text = result.stdout.strip()
    if not diff_text:
        return None, "no changes detected between HEAD~1 and HEAD."

    return diff_text[:MAX_DIFF_CHARS], None


def build_prompt(diff_text: str) -> str:
    return (
        "You are a senior DevOps engineer.\n"
        "Analyze the following git diff and respond in EXACTLY this format:\n\n"
        "COMMIT_MESSAGE:\n"
        "<one conventional commit message, max 72 characters>\n\n"
        "CHANGELOG:\n"
        "<2-3 bullet points in Markdown>\n\n"
        "Do not add explanations or extra text.\n\n"
        f"{diff_text}\n"
    )


def parse_ollama_stream(stream_lines) -> str:
    parts = []
    for raw_line in stream_lines:
        line = raw_line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if payload.get("message", {}).get("content"):
            parts.append(payload["message"]["content"])
    return "".join(parts).strip()


def call_ollama(prompt: str) -> Tuple[Optional[str], Optional[str]]:
    host = os.getenv("OLLAMA_HOST", DEFAULT_OLLAMA_HOST)
    model = os.getenv("MODEL_NAME", DEFAULT_MODEL_NAME)

    url = f"{host.rstrip('/')}/api/chat"
    payload = {
        "model": model,
        "stream": True,
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
    }

    try:
        response = requests.post(url, json=payload, stream=True, timeout=60)
    except requests.RequestException as exc:
        return None, f"failed to reach Ollama at {url}: {exc}"

    if response.status_code != 200:
        return None, f"Ollama returned HTTP {response.status_code}: {response.text.strip()}"

    content = parse_ollama_stream(response.iter_lines(decode_unicode=True))
    if not content:
        return None, "received empty response from Ollama."

    return content, None


def split_output(content: str) -> Tuple[str, str]:
    commit_message = "chore: update changes"
    changelog = "- Updated recent changes."

    lines = content.splitlines()
    current_section = None
    changelog_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.upper().startswith("COMMIT_MESSAGE"):
            current_section = "commit"
            continue

        if line.upper().startswith("CHANGELOG"):
            current_section = "changelog"
            continue

        if current_section == "commit" and commit_message.startswith("chore"):
            commit_message = line
        elif current_section == "changelog":
            changelog_lines.append(line)

    if changelog_lines:
        changelog = "\n".join(changelog_lines)

    return commit_message, changelog


def main() -> int:
    diff_text, error = run_git_diff()
    if error:
        print(error)
        return 1

    prompt = build_prompt(diff_text)
    response_text, error = call_ollama(prompt)
    if error:
        print(error)
        return 0

    commit_message, changelog = split_output(response_text)

    print("-------------------------")
    print("Commit Message:")
    print(commit_message)
    print()
    print("Changelog:")
    print(f"### Unreleased {DEFAULT_VERSION} ({date.today().isoformat()})")
    print(changelog)
    print("-------------------------")
    return 0


if __name__ == "__main__":
    sys.exit(main())
