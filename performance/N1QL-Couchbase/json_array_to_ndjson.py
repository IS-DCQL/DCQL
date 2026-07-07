#!/usr/bin/env python3
"""Helper utilities for reading the converted JSON collection files.

Two roles:
  1. `iter_json_docs(path)` -- imported by 2_load.py to stream documents out of a file that
     may be a JSON array, a single JSON object, or NDJSON. (Folded in from the original
     import_material.py loader so the load script stays self-contained.)
  2. CLI `stream_json_array_to_ndjson(...)` -- the original standalone converter that turns a
     big top-level JSON array into NDJSON line-by-line (memory-safe, via ijson). Kept for
     pre-flattening very large raw arrays before loading.
"""
import json
import os
import sys
import time
from pathlib import Path


# ===== importable doc iterator (JSON array / single object / NDJSON) =====
def iter_json_docs(file_path):
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"file not found: {file_path}")

    # peek first non-space char
    first_char = ""
    with open(path, "r", encoding="utf-8") as f:
        while True:
            ch = f.read(1)
            if not ch:
                break
            if not ch.isspace():
                first_char = ch
                break

    if first_char in ["[", "{"]:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    yield item
        elif isinstance(data, dict):
            for key in ["data", "records", "items", "documents", "samples"]:
                value = data.get(key)
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            yield item
                    return
            yield data
        else:
            raise ValueError(f"unsupported top-level JSON: {type(data)}")
    else:
        with open(path, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    doc = json.loads(line)
                except json.JSONDecodeError as e:
                    print(f"line {line_no} JSON parse failed, skipped: {e}")
                    continue
                if isinstance(doc, dict):
                    yield doc


# ===== standalone streaming JSON-array -> NDJSON converter =====
def format_bytes(num: float) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
        if num < 1024.0:
            return f"{num:.2f}{unit}"
        num /= 1024.0
    return f"{num:.2f}EB"


def format_seconds(seconds: float) -> str:
    if seconds <= 0 or seconds == float("inf"):
        return "--:--:--"
    seconds = int(seconds)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def print_progress(current_bytes, total_bytes, count, start_time):
    elapsed = time.time() - start_time
    percent = (current_bytes / total_bytes * 100) if total_bytes > 0 else 0
    speed_bytes = current_bytes / elapsed if elapsed > 0 else 0
    speed_records = count / elapsed if elapsed > 0 else 0
    remaining = total_bytes - current_bytes
    eta = remaining / speed_bytes if speed_bytes > 0 else float("inf")
    print(
        f"\rprogress: {percent:6.2f}% | "
        f"read: {format_bytes(current_bytes)}/{format_bytes(total_bytes)} | "
        f"records: {count} | "
        f"speed: {format_bytes(speed_bytes)}/s, {speed_records:.1f}/s | "
        f"elapsed: {format_seconds(elapsed)} | ETA: {format_seconds(eta)}",
        end="", flush=True,
    )


def stream_json_array_to_ndjson(input_path, output_path, ensure_ascii=False,
                                progress_interval=0.5, flush_every=5000):
    """Convert a top-level JSON array to NDJSON (streaming, memory-safe)."""
    try:
        import ijson
    except ImportError:
        print("ijson not installed; run: pip install ijson", file=sys.stderr)
        sys.exit(3)

    total_size = os.path.getsize(input_path)
    start_time = time.time()
    last_progress_time = 0
    count = 0
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(input_path, "rb") as fin, \
            open(output_path, "w", encoding="utf-8", newline="\n") as fout:
        try:
            for obj in ijson.items(fin, "item", use_float=True):
                fout.write(json.dumps(obj, ensure_ascii=ensure_ascii,
                                      separators=(",", ":")) + "\n")
                count += 1
                if flush_every > 0 and count % flush_every == 0:
                    fout.flush()
                now = time.time()
                if now - last_progress_time >= progress_interval:
                    print_progress(fin.tell(), total_size, count, start_time)
                    last_progress_time = now
        except ijson.JSONError as e:
            print()
            raise ValueError(f"JSON parse failed (not a top-level array?): {e}") from e

    print_progress(total_size, total_size, count, start_time)
    print()
    return count


def main():
    if len(sys.argv) != 3:
        print("usage: python3 json_array_to_ndjson.py <input.json> <output.ndjson>",
              file=sys.stderr)
        sys.exit(1)
    input_path, output_path = sys.argv[1], sys.argv[2]
    if not os.path.exists(input_path):
        print(f"input not found: {input_path}", file=sys.stderr)
        sys.exit(1)
    count = stream_json_array_to_ndjson(input_path, output_path)
    print(f"done: wrote {count} records -> {output_path}")


if __name__ == "__main__":
    main()
