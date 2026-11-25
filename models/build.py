"""Build the static GitHub Pages output for every model lab.

Import each ``models/labs/<lab>/source.py``, run its sources in parallel across
labs, and write ``<out>/models/<lab>/index.json`` for every lab plus
``<out>/models/index.json`` with the list of labs and the status of their sources.

Usage: ``python -m models.build [--out _site] [--workers 8] [--only lab1,lab2]``
"""

import argparse
import importlib
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from models.common.runner import run_lab, to_json, utc_now
from models.common.validation import require_positive_number, require_type

LABS_DIR = Path(__file__).parent / "labs"

DEFAULT_WORKERS = 8


def discover_labs() -> list[str]:
	"""Return the names of all lab folders that contain a ``source.py``.

	Returns:
		list[str]: Lab names in alphabetical order.
	"""

	return sorted(path.parent.name for path in LABS_DIR.glob("*/source.py"))


def build_lab(lab: str) -> dict:
	"""Import a lab's ``source.py`` and run its sources.

	Args:
		lab (str): Lab folder name.

	Returns:
		dict: Document from ``run_lab``.
	"""

	require_type("lab", lab, str)

	module = importlib.import_module(f"models.labs.{lab}.source")

	return run_lab(lab, module.SOURCES)


def summary_entry(document: dict) -> dict:
	"""Return the index entry for one lab document.

	Args:
		document (dict): Document from ``run_lab``.

	Returns:
		dict: Lab name, relative URL, generation time and per-source status.
	"""

	require_type("document", document, dict)

	sources = [{"rank": s["rank"], "type": s["type"], "status": s["status"], "error": s["error"]} for s in document["sources"]]

	return {"lab": document["lab"], "url": f"{document['lab']}/index.json", "generated_at": document["generated_at"], "sources": sources}


def write_json(path: Path, text: str) -> None:
	"""Write JSON text to ``path``, creating parent folders.

	Args:
		path (Path): Target file.
		text (str): JSON text.

	Returns:
		None
	"""

	require_type("path", path, Path)
	require_type("text", text, str)

	path.parent.mkdir(parents=True, exist_ok=True)
	path.write_text(text + "\n", encoding="utf-8", newline="\n")


def build(out_dir: Path, labs: list[str], workers: int) -> list[dict]:
	"""Run the given labs in parallel and write their JSON files under ``out_dir``.

	Args:
		out_dir (Path): Site root, e.g. ``_site``.
		labs (list[str]): Lab names to build.
		workers (int): Maximum number of labs fetched at the same time.

	Returns:
		list[dict]: Index entries, one per lab.
	"""

	require_type("out_dir", out_dir, Path)
	require_type("labs", labs, list)
	require_type("workers", workers, int)
	require_positive_number("workers", workers)

	unknown = sorted(set(labs) - set(discover_labs()))

	if unknown:
		raise ValueError(f"unknown labs: {unknown}")

	max_workers = min(workers, os.cpu_count() or 1, len(labs))

	with ThreadPoolExecutor(max_workers=max_workers) as pool:
		documents = list(pool.map(build_lab, labs))

	models_dir = out_dir / "models"

	for document in documents:
		write_json(models_dir / document["lab"] / "index.json", to_json(document))

	entries = [summary_entry(document) for document in documents]
	write_json(models_dir / "index.json", to_json({"generated_at": utc_now(), "labs": entries}))

	return entries


def main() -> None:
	"""Parse the command line, build the site and print one status line per lab."""

	parser = argparse.ArgumentParser(description="Build the GitHub Pages output for the model labs.")
	parser.add_argument("--out", type=Path, default=Path("_site"), help="output folder (site root)")
	parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS, help="labs fetched in parallel")
	parser.add_argument("--only", default="", help="comma-separated lab names; default is every lab")
	args = parser.parse_args()

	labs = [name.strip() for name in args.only.split(",") if name.strip()] or discover_labs()
	entries = build(args.out, labs, args.workers)

	sys.stdout.reconfigure(encoding="utf-8")

	for entry in entries:
		marks = " ".join(f"{s['rank']}:{s['type']}:{s['status']}" + (f" ({s['error']})" if s["error"] else "") for s in entry["sources"])
		print(f"{entry['lab']:16} {marks}")


if __name__ == "__main__":
	main()
