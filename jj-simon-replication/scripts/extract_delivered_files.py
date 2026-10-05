"""Recover research files delivered by child sessions as cross-session
messages ("=== FILE <path> PART i/n ===" blocks) from this session's local
transcript, and write them into the repository. Run from jj-simon-replication/:

    python scripts/extract_delivered_files.py /root/.claude/projects/<project>/<session>.jsonl
"""
from __future__ import annotations

import html
import json
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
BLOCK = re.compile(r"^[ \t]*=== FILE (\S+) PART (\d+)/(\d+) ===[ \t]*\n(.*?)(?=^[ \t]*=== (?:FILE|DONE) |\Z)", re.S | re.M)


def iter_strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from iter_strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from iter_strings(v)


def dedent(block: str) -> str:
    lines = block.split("\n")
    indents = [len(l) - len(l.lstrip(" ")) for l in lines if l.strip()]
    k = min(indents) if indents else 0
    return "\n".join(l[k:] if len(l) >= k else l for l in lines)


def main(path: str) -> int:
    parts: dict[str, dict[int, tuple[int, str]]] = defaultdict(dict)
    with open(path, errors="replace") as fh:
        for line in fh:
            if "=== FILE " not in line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            for s in iter_strings(obj):
                if "=== FILE " not in s:
                    continue
                text = s.replace("</cross-session-message>", "\n=== DONE ===")
                for m in BLOCK.finditer(text):
                    rel, i, n, body = m.group(1), int(m.group(2)), int(m.group(3)), m.group(4)
                    body = html.unescape(dedent(body)).rstrip("\n") + "\n"
                    parts[rel][i] = (n, body)
    written = 0
    for rel, chunks in parts.items():
        n = max(v[0] for v in chunks.values())
        if any(i not in chunks for i in range(1, n + 1)):
            print(f"incomplete: {rel} has {sorted(chunks)} of {n}")
            continue
        content = "".join(chunks[i][1] for i in range(1, n + 1))
        if rel.endswith(".json"):
            try:
                content = json.dumps(json.loads(content), indent=1, ensure_ascii=False) + "\n"
            except json.JSONDecodeError as e:
                print(f"invalid json in {rel}: {e}; writing raw")
        out = os.path.join(REPO, rel)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w") as fh:
            fh.write(content)
        written += 1
        print(f"wrote {rel} ({len(content)} chars, {n} part(s))")
    print(f"{written} files written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
