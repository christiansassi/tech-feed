"""Read every news source and publish the items of the last two days as raw JSON.

For each source in ``news/sources.py``, fetch it with the shared source runner,
keep the items dated within ``WINDOW_HOURS`` and write them, newest first, to
``<out>/news/raw/latest.json``. The Raspberry updater calls ``build`` with its
site folder every hour, then filters the items with Codex. ``<out>/news/index.json`` lists every source
with its fetch status and item counts, the raw file and the site file
(``site/latest.json``, written by the Raspberry updater after the Codex filters).
Items without a date are left out, since the site shows only the last 24 hours.

Usage: ``python -m news.build [--out _site] [--workers 8]``
"""

import argparse
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from models.common.runner import run_lab, to_json, utc_now
from models.common.validation import require_positive_number, require_text, require_type
from news.sources import SOURCES, NewsSource

DEFAULT_WORKERS = 8

# Twice the 24 hours shown on the site, so an item published late in a feed still reaches the updater.
WINDOW_HOURS = 48

def read_source(news_source: NewsSource) -> dict:
	"""Fetch one news source and return its status and its items at the ``medium`` level.

	Args:
		news_source (NewsSource): Source to read.

	Returns:
		dict: ``slug``, ``label``, ``url``, ``type``, ``status``, ``error`` and ``items``.
	"""

	require_type("news_source", news_source, NewsSource)

	entry = run_lab(news_source.slug, news_source.label, [news_source.source])["sources"][0]
	items = [{key: value for key, value in item.items() if key != "body"} for item in entry["items"]]

	return {"slug": news_source.slug, "label": news_source.label, "url": entry["url"], "type": entry["type"], "status": entry["status"], "error": entry["error"], "items": items}

def write_json(path: Path, text: str) -> None:
	"""Write JSON text to ``path``, creating parent folders.

	Args:
		path (Path): Target file.
		text (str): JSON text.

	Returns:
		None
	"""

	require_type("path", path, Path)
	require_text("text", text)

	path.parent.mkdir(parents=True, exist_ok=True)
	path.write_text(text + "\n", encoding="utf-8", newline="\n")

def collect(workers: int) -> dict:
	"""Read every source in parallel and return the items of the last ``WINDOW_HOURS`` with the status of each source.

	Args:
		workers (int): Maximum number of sources fetched at the same time.

	Returns:
		dict: ``generated_at``, ``items`` (newest first, each with its source ``slug`` as ``source`` and its publisher ``label``) and ``sources`` (one index entry per source).
	"""

	require_type("workers", workers, int)
	require_positive_number("workers", workers)

	with ThreadPoolExecutor(max_workers=min(workers, os.cpu_count() or 1)) as pool:
		results = list(pool.map(read_source, SOURCES))

	now = utc_now()
	oldest = now - WINDOW_HOURS * 3600
	items = []
	entries = []

	for result in results:
		recent = [item for item in result["items"] if isinstance(item["date"], int) and oldest <= item["date"] <= now + 3600]
		undated = sum(1 for item in result["items"] if not isinstance(item["date"], int))

		items.extend({"source": result["slug"], "label": result["label"], **item} for item in recent)
		entries.append({key: result[key] for key in ("slug", "label", "url", "type", "status", "error")} | {"items": len(result["items"]), "recent": len(recent), "undated": undated})

	items.sort(key=lambda item: item["date"], reverse=True)

	return {"generated_at": now, "items": items, "sources": entries}

def build(out_dir: Path, workers: int) -> dict:
	"""Read every source and write the raw file and the index under ``out_dir``.

	Args:
		out_dir (Path): Site root, e.g. ``_site``.
		workers (int): Maximum number of sources fetched at the same time.

	Returns:
		dict: The collected document from ``collect``.
	"""

	require_type("out_dir", out_dir, Path)

	document = collect(workers)
	news_dir = out_dir / "news"

	write_json(news_dir / "raw" / "latest.json", to_json({"generated_at": document["generated_at"], "window_hours": WINDOW_HOURS, "items": document["items"]}))
	write_json(news_dir / "index.json", to_json({"generated_at": document["generated_at"], "raw": "raw/latest.json", "site": "site/latest.json", "sources": document["sources"]}))

	return document

def main() -> None:
	"""Parse the command line, build the raw news file and print one status line per source."""

	parser = argparse.ArgumentParser(description="Build the raw news file for the GitHub Pages site.")
	parser.add_argument("--out", type=Path, default=Path("_site"), help="output folder (site root)")
	parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS, help="sources fetched in parallel")
	args = parser.parse_args()

	entries = build(args.out, args.workers)["sources"]

	sys.stdout.reconfigure(encoding="utf-8")

	for entry in entries:
		print(f"{entry['slug']:30} {entry['status']:5} {entry['items']:4} items {entry['recent']:3} recent {entry['undated']:3} undated" + (f"  ({entry['error']})" if entry["error"] else ""))

if __name__ == "__main__":
	main()
