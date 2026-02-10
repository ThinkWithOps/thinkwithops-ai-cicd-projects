#!/usr/bin/env python3
import argparse
import os
import subprocess
try:
    from langchain_ollama import OllamaLLM
    from langchain_core.prompts import PromptTemplate
    from langchain_core.output_parsers import StrOutputParser
except ModuleNotFoundError as exc:
    raise SystemExit(
        "Missing dependency. Run:\n"
        "python -m pip install -r requirements.txt\n"
        "python -m pip install langchain-ollama\n"
        f"Original error: {exc}"
    )


def review_code(diff: str) -> str:
    model_name = os.getenv("OLLAMA_MODEL", "phi3")
    llm = OllamaLLM(model=model_name, temperature=0.1)

    with open("prompts/review_prompt.txt", encoding="utf-8") as f:
        template = PromptTemplate.from_template(f.read())

    chain = template | llm | StrOutputParser()
    return chain.invoke({"diff": diff}).strip()


def get_git_diff(staged: bool) -> str:
    """Return git diff from current repository."""
    cmd = ["git", "diff", "--cached"] if staged else ["git", "diff"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Failed to read git diff")
    return result.stdout.strip()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run local AI code review")
    parser.add_argument(
        "--diff-file",
        default="",
        help="Path to patch file (e.g., sample_diff.patch). If omitted, reads git diff.",
    )
    parser.add_argument(
        "--staged",
        action="store_true",
        help="Use staged diff (git diff --cached). Default is unstaged diff.",
    )
    args = parser.parse_args()

    if args.diff_file:
        with open(args.diff_file, encoding="utf-8") as f:
            diff = f.read()
        source = f"file: {args.diff_file}"
    else:
        diff = get_git_diff(staged=args.staged)
        source = "git staged diff" if args.staged else "git working diff"

    if not diff.strip():
        raise SystemExit(f"No changes found in {source}.")

    review = review_code(diff)
    print("\n" + "=" * 50)
    print("AI CODE REVIEW")
    print("=" * 50)
    print(f"Source: {source}")
    print("-" * 50)
    print(review)
    print("=" * 50)
