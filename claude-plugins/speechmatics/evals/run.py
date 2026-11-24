#!/usr/bin/env python3
"""Run the skill evals against a local install of the speechmatics plugin.

Each case in cases/<skill>.json is a prompt sent to `claude -p` in an empty
directory. A case passes when Claude loads the expected skill (or one of them,
when `expected_skill` is a list) and the answer
matches every regex in `must_match`.

Usage:
    python3 run.py                # all cases
    python3 run.py batch agent    # only case files whose name contains a filter
    JOBS=8 python3 run.py         # parallelism (default 4)
"""

import json
import os
import re
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).parent
PLUGIN = "speechmatics"
TIMEOUT = 300


def load_cases(filters):
    cases = []
    for path in sorted((HERE / "cases").glob("*.json")):
        if filters and not any(f in path.stem for f in filters):
            continue
        for i, case in enumerate(json.loads(path.read_text())):
            cases.append({**case, "id": f"{path.stem}#{i + 1}"})
    return cases


def run_case(case):
    skills, texts, error = [], [], None
    with tempfile.TemporaryDirectory() as cwd:
        try:
            proc = subprocess.run(
                [
                    "claude",
                    "-p",
                    case["prompt"],
                    "--output-format",
                    "stream-json",
                    "--verbose",
                    # Skills keep detail in references/; let Claude read them.
                    "--allowedTools",
                    "Read,Grep,Glob",
                ],
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=TIMEOUT,
            )
        except subprocess.TimeoutExpired:
            return {**case, "skills": [], "answer": "", "missing": [], "ok": False, "error": "timeout"}
    for line in proc.stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "assistant":
            for block in event["message"]["content"]:
                if block["type"] == "tool_use" and block["name"] == "Skill":
                    skills.append(block["input"].get("skill", ""))
                elif block["type"] == "text":
                    texts.append(block["text"])
        elif event.get("type") == "result" and event.get("subtype") != "success":
            error = event.get("subtype")
    answer = "\n".join(texts)
    expected = case["expected_skill"]
    expected = [expected] if isinstance(expected, str) else expected
    missing = [p for p in case["must_match"] if not re.search(p, answer, re.I | re.S)]
    triggered = any(f"{PLUGIN}:{name}" in skills for name in expected)
    return {
        **case,
        "skills": skills,
        "answer": answer,
        "missing": missing,
        "triggered": triggered,
        "ok": triggered and not missing and not error,
        "error": error,
    }


def main():
    cases = load_cases(sys.argv[1:])
    jobs = int(os.environ.get("JOBS", "4"))
    with ThreadPoolExecutor(jobs) as pool:
        results = list(pool.map(run_case, cases))
    for r in results:
        status = "PASS" if r["ok"] else "FAIL"
        print(f"{status} {r['id']}: {r['prompt'][:70]}")
        if not r["ok"]:
            print(f"     skills loaded: {r['skills'] or 'none'}")
            if r["missing"]:
                print(f"     missing: {r['missing']}")
            if r.get("error"):
                print(f"     error: {r['error']}")
    passed = sum(r["ok"] for r in results)
    print(f"\n{passed}/{len(results)} passed")
    out = Path(os.environ.get("EVAL_OUT", tempfile.gettempdir())) / "speechmatics-evals.json"
    out.write_text(json.dumps(results, indent=2))
    print(f"Full answers: {out}")
    sys.exit(0 if passed == len(results) else 1)


if __name__ == "__main__":
    main()
