"""Bounded, read-only Markdown retrieval. Python standard library only."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1] / "references"
DISABLED = {"mentors/fds_papers.md"}


class RetrievalError(ValueError):
    def __init__(self, message, **details):
        super().__init__(message)
        self.details = details


def document(root, name):
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()) or path.suffix != ".md":
        raise ValueError("Select a Markdown file inside references.")
    relative = path.relative_to(root.resolve()).as_posix()
    if relative in DISABLED:
        raise ValueError("This corpus is disabled.")
    raw = path.read_bytes()
    lines = raw.decode("utf-8-sig").splitlines()
    headings, fence = [], None
    for i, line in enumerate(lines):
        marker = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
        if marker:
            run = marker.group(1)
            if fence is None:
                fence = run
            elif run[0] == fence[0] and len(run) >= len(fence):
                fence = None
            continue
        match = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", line)
        if match and fence is None:
            headings.append({"line": i + 1, "level": len(match[1]), "title": match[2]})
    digest = hashlib.sha256(raw).hexdigest()
    stack = []
    for i, heading in enumerate(headings):
        while stack and stack[-1]["level"] >= heading["level"]:
            stack.pop()
        heading["path"] = [h["title"] for h in stack] + [heading["title"]]
        heading["parent_line"] = stack[-1]["line"] if stack else None
        heading["id"] = f"@{digest}:{heading['line']}"
        stack.append(heading)
        heading["end"] = next((h["line"] - 1 for h in headings[i + 1:]
                               if h["level"] <= heading["level"]), len(lines))
    return relative, lines, headings, digest


def catalog(root, name, query=""):
    relative, _, headings, digest = document(root, name)
    terms = query.casefold().split()
    return {"file": relative, "sha256": digest, "sections": [h for h in headings
            if all(term in h["title"].casefold() for term in terms)]}


def select_heading(headings, selector):
    if selector.startswith("@"):
        match = re.fullmatch(r"@([0-9a-f]{64}):(\d+)", selector)
        if not match:
            raise RetrievalError("Invalid section ID; copy an ID from catalog.", kind="invalid_id")
        if headings and match[1] != headings[0]["id"][1:65]:
            raise RetrievalError("File version changed; refresh catalog before reading.", kind="stale_id")
        matches = [h for h in headings if h["id"] == selector]
    elif selector.startswith("path:"):
        try:
            path = json.loads(selector[5:])
        except ValueError as exc:
            raise RetrievalError("Path must be a JSON array of exact headings.", kind="invalid_path") from exc
        if not isinstance(path, list) or not all(isinstance(part, str) for part in path):
            raise RetrievalError("Path must be a JSON array of exact headings.", kind="invalid_path")
        matches = [h for h in headings if h["path"] == path]
    else:
        exact = [h for h in headings if h["title"] == selector]
        matches = exact or [h for h in headings if re.match(
            r"^" + re.escape(selector) + r"(?=\s|[.、]\s|$)", h["title"])]
    if len(matches) != 1:
        raise RetrievalError("Section selector must match exactly once: " + selector,
                             kind="ambiguous" if matches else "not_found", candidates=matches)
    return matches[0]


def ranges(lines, headings, targets):
    spans = []
    if headings and headings[0]["line"] > 1:
        spans.append((1, headings[0]["line"] - 1))
    for target in targets:
        spans.append((target["line"], target["end"]))
        for i, ancestor in enumerate(headings):
            if ancestor["line"] < target["line"] <= ancestor["end"]:
                intro_end = headings[i + 1]["line"] - 1 if i + 1 < len(headings) else len(lines)
                spans.append((ancestor["line"], intro_end))
    merged = []
    for start, end in sorted(set(spans)):
        if merged and start <= merged[-1][1] + 1:
            merged[-1][1] = max(end, merged[-1][1])
        else:
            merged.append([start, end])
    return merged


def range_size(lines, spans):
    return sum(len("\n".join(lines[start - 1:end])) for start, end in spans)


def read_packet(root, selectors, max_chars=24000):
    grouped = {}
    for value in selectors:
        name, sep, selector = value.partition("::")
        if not sep or not selector:
            raise ValueError("Use file.md::section-title-or-number; use * for a whole small file.")
        grouped.setdefault(name, []).append(selector)
    if max_chars <= 0:
        raise ValueError("--max-chars must be positive.")
    files, selection_context = [], []
    for name, wanted in grouped.items():
        relative, lines, headings, digest = document(root, name)
        targets = []
        try:
            # Validate every supplied ID even when * is also requested.
            targets = [select_heading(headings, s) for s in wanted if s != "*"]
        except RetrievalError as error:
            error.details["file"] = relative
            error.details["sha256"] = digest
            raise
        whole = "*" in wanted
        merged = [[1, len(lines)]] if whole else ranges(lines, headings, targets)
        files.append({"file": relative, "sha256": digest, "excerpts": [
            {"start_line": start, "end_line": end, "text": "\n".join(lines[start - 1:end])}
            for start, end in merged]})
        selection_context.append((relative, lines, headings, targets, whole))
    size = sum(len(e["text"]) for f in files for e in f["excerpts"])
    if size > max_chars:
        candidates = []
        for relative, lines, headings, targets, whole in selection_context:
            parents = {h["line"] for h in targets}
            children = [h for h in headings if h["parent_line"] in parents]
            if whole:
                children = [h for h in headings if h["parent_line"] is None]
                if len(children) == 1:
                    children = [h for h in headings if h["parent_line"] == children[0]["line"]] or children
            # Keep leaves too, so oversized batches can be split without another lookup.
            children += [h for h in targets if not any(c["parent_line"] == h["line"] for c in headings)]
            seen = set()
            for h in children:
                if h["id"] in seen:
                    continue
                seen.add(h["id"])
                chars = range_size(lines, ranges(lines, headings, [h]))
                candidates.append({"file": relative, "id": h["id"], "path": h["path"],
                                   "selector": relative + "::" + h["id"],
                                   "text_chars": chars, "fits_budget": chars <= max_chars})
        raise RetrievalError(
            f"Selected {size} characters exceeds {max_chars}; select smaller sections or explicitly raise --max-chars. No text was truncated.",
            kind="over_limit", text_chars=size, max_chars=max_chars, candidates=candidates,
            next_step="Select relevant children or split the batch. Oversized leaf sections require an explicit larger budget; no text was truncated.")
    return {"text_chars": size, "files": files,
            "scope": "Selected sections and ancestor introductions only. Read linked rules/source sections when needed; absence here does not mean absence from the corpus."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ascii", action="store_true", help="Escaped JSON fallback for broken Unicode transports")
    sub = parser.add_subparsers(dest="command", required=True)
    cat = sub.add_parser("catalog")
    cat.add_argument("--file", required=True)
    cat.add_argument("--query", default="")
    read = sub.add_parser("read")
    read.add_argument("--select", action="append", required=True)
    read.add_argument("--max-chars", type=int, default=24000)
    args = parser.parse_args()
    try:
        result = catalog(ROOT, args.file, args.query) if args.command == "catalog" else read_packet(ROOT, args.select, args.max_chars)
        code = 0
    except RetrievalError as error:
        result, code = {"error": str(error), **error.details}, 2
    except (ValueError, OSError, UnicodeError) as error:
        result, code = {"error": str(error)}, 2
    sys.stdout.buffer.write((json.dumps(result, ensure_ascii=args.ascii, indent=2) + "\n").encode("utf-8"))
    return code


if __name__ == "__main__":
    sys.exit(main())
