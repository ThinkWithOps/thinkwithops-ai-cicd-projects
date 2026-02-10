#!/usr/bin/env python3
import os
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


if __name__ == "__main__":
    # Load diff from file (for local dry run)
    with open("sample_diff.patch", encoding="utf-8") as f:
        diff = f.read()

    review = review_code(diff)
    print("\n" + "=" * 50)
    print("AI CODE REVIEW")
    print("=" * 50)
    print(review)
    print("=" * 50)
