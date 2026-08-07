#!/usr/bin/env python3
import json
import os
import subprocess
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def ensure_files_exist(repo_root: Path = REPO_ROOT):
    for rel in ["README.md", "calculator.html"]:
        path = repo_root / rel
        if not path.exists():
            raise FileNotFoundError(f"Missing required file: {rel}")


def write_report(summary: str, repo_root: Path = REPO_ROOT):
    report_path = repo_root / "ai-improvement-report.txt"
    report_path.write_text(summary, encoding="utf-8")


def build_prompt(repo_context: str) -> str:
    return (
        "You are operating inside a small repository. Analyze the codebase and suggest "
        "practical improvements. If there is a README, improve it. If there is HTML/CSS/JS, "
        "make safe, minimal enhancements. Avoid destructive changes. Output a concise summary "
        "of what you changed.\n\nRepository context:\n" + repo_context
    )


def try_local_ollama(prompt: str, model: str, repo_root: Path = REPO_ROOT) -> str:
    host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode("utf-8")

    try:
        req = urllib.request.Request(
            f"{host}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as response:
            body = json.loads(response.read().decode("utf-8"))
            return body.get("response", "").strip()
    except Exception as exc:
        print(f"Ollama request failed: {exc}")
        return ""


def apply_fallback_improvement(repo_root: Path = REPO_ROOT) -> str:
    readme_path = repo_root / "README.md"
    readme_text = readme_path.read_text(encoding="utf-8")
    if "Auto-improved by OpenCode workflow" not in readme_text:
        readme_path.write_text(
            readme_text + "\n\nAuto-improved by OpenCode workflow. This repository is monitored for changes and can be enhanced automatically using a free local model.\n",
            encoding="utf-8",
        )
    return "Applied a safe fallback improvement to the repository README."


def main():
    ensure_files_exist()

    with open(REPO_ROOT / "README.md", "r", encoding="utf-8") as fh:
        repo_context = fh.read()

    prompt = build_prompt(repo_context)
    model = os.getenv("OLLAMA_MODEL", "qwen2.5:3b-instruct")
    ai_summary = try_local_ollama(prompt, model)

    if ai_summary:
        write_report(ai_summary)
        print("Local free model response received.")
        return

    summary = apply_fallback_improvement()
    write_report(summary)
    print("No free local model response was available; used fallback improvement.")


if __name__ == "__main__":
    main()
