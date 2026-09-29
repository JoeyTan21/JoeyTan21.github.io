#!/usr/bin/env python3
"""Regenerate the pull-request table on open-source/index.html.

Fetches each PR's current state with the GitHub CLI (`gh`), so merged PRs
flip to MERGED automatically. Run from the repo root:

    python3 scripts/update_prs.py

Edit the PRS list below to add a PR or reword its one-line description.
"""
import html
import json
import re
import subprocess
import sys
from pathlib import Path

# (owner/repo, PR number, one-line description of the fix)
PRS = [
    ("huggingface/transformers", 49136,
     "get_json_schema dropped items/enum when flattening unions of list, dict and Literal types"),
    ("pydantic/pydantic-ai", 8848,
     "application/toml is now text-like, so TOML BinaryContent is inlined instead of rejected"),
    ("mlflow/mlflow", 26260,
     "Schema inference failed or silently degraded to Any depending on where a None value appeared"),
    ("huggingface/trl", 7446,
     "SFTTrainer never appended EOS when dataset_text_field was set to anything other than \"text\""),
    ("huggingface/pytorch-image-models", 2817,
     "list_models(exclude_filters='<str>') iterated the string per character and excluded everything"),
    ("huggingface/accelerate", 4354,
     "wait_for_everyone() crashed on MULTI_CPU when the machine has a non-CUDA accelerator (MPS)"),
    ("docling-project/docling", 4430,
     "Path inputs with an upper-case extension (notes.VTT) were rejected as an unknown format"),
    ("huggingface/datasets", 8701,
     "ArrayXD columns could not round-trip from pandas back to Arrow (adds __arrow_array__)"),
    ("agno-agi/agno", 10627,
     "get_sessions(session_name=...) raised on sessions whose name is None in dict-based DBs"),
    ("run-llama/llama_index", 23268,
     "LLMMultiSelector appended the output-format instructions to the prompt twice"),
    ("stanfordnlp/dspy", 10512,
     "Custom type markers leaked into assistant and system messages from demos and history"),
    ("wxt-dev/wxt", 2602,
     "Create the configured Chromium profile before launch instead of failing when it is missing"),
    ("SeekingDream/DLCompilerAttack", 3,
     "Generalized Attacker API so the compiler backdoor attack works on arbitrary models"),
    ("kamillobinski/thock", 107,
     "Bluetooth audio artifacts and idle-queue noise in a macOS keyboard-sound app (Swift)"),
]

STATUS_ORDER = {"MERGED": 0, "OPEN": 1, "CLOSED": 2}
PAGE = Path(__file__).resolve().parent.parent / "open-source" / "index.html"


def fetch_state(repo: str, number: int) -> str:
    try:
        out = subprocess.run(
            ["gh", "pr", "view", str(number), "-R", repo, "--json", "state"],
            check=True, capture_output=True, text=True,
        ).stdout
        return json.loads(out)["state"]
    except (subprocess.CalledProcessError, FileNotFoundError, KeyError, json.JSONDecodeError) as e:
        print(f"warning: could not fetch {repo}#{number} ({e}); marking OPEN", file=sys.stderr)
        return "OPEN"


def main() -> None:
    rows = []
    for repo, number, desc in PRS:
        state = fetch_state(repo, number)
        rows.append((STATUS_ORDER.get(state, 9), repo, number, desc, state))
    rows.sort(key=lambda r: r[0])  # stable: merged first, then list order

    lines = []
    for _, repo, number, desc, state in rows:
        url = f"https://github.com/{repo}/pull/{number}"
        lines.append(
            "      <li>\n"
            f"        <a class=\"title\" href=\"{url}\" target=\"_blank\" rel=\"noopener\">{html.escape(repo)} <span class=\"pr-num\">#{number}</span></a>\n"
            f"        <span class=\"author\">{html.escape(desc)}</span>\n"
            f"        <span class=\"status status-{state.lower()}\">{state.title()}</span>\n"
            "      </li>"
        )
    block = "\n".join(lines)

    src = PAGE.read_text()
    new = re.sub(
        r"(<!-- prs:start[^>]*-->\n).*?(\s*<!-- prs:end -->)",
        lambda m: m.group(1) + block + "\n" + m.group(2).lstrip("\n"),
        src, flags=re.S,
    )
    PAGE.write_text(new)
    merged = sum(1 for r in rows if r[4] == "MERGED")
    print(f"wrote {len(rows)} PRs ({merged} merged) to {PAGE.relative_to(PAGE.parents[1])}")


if __name__ == "__main__":
    main()
