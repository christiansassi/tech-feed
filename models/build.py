"""Build the static GitHub Pages output for every model lab.

Import each ``models/labs/<lab>/source.py``, run its sources in parallel across
labs, and write ``<out>/models/<lab>/raw/light.json``, ``medium.json`` and
``full.json`` for every followed lab, plus ``<out>/models/index.json`` with the list of
followed labs, their file URLs and the status of their sources, and the labs whose code is kept but whose data is not built. The index also names
``<lab>/site/latest.json``, the latest models shown on the site, which the
Raspberry updater publishes on the ``site-data`` branch and the workflow copies
into the site. When ``DEFAULT_LEVEL`` is set, that level is also written as
``<out>/models/<lab>/index.json`` so the bare folder URL answers with it.

With ``--deep`` the sources are read in deep mode (no byte budget, every page of
paginated sources, more Hugging Face models), for a one-off history backfill.

Usage: ``python -m models.build [--out _site] [--workers 8] [--only lab1,lab2] [--deep]``
"""

import argparse
import importlib
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from models.common.items import LEVELS
from models.common.runner import at_document_level, run_lab, to_json, utc_now
from models.common.sources import DEEP_ENV
from models.common.validation import require_positive_number, require_type

LABS_DIR = Path(__file__).parent / "labs"

DEFAULT_WORKERS = 8

DEFAULT_LEVEL = None

# Labs built and analyzed every hour; the other labs keep their code but get no data.
TRACKED = frozenset({"anthropic", "deepseek", "google", "meta", "minimax", "mistral", "moonshotai", "openai", "qwen", "tencent", "thinkingmachines", "xai", "xiaomi", "zai"})

def discover_labs() -> list[str]:
	"""Return the names of all lab folders that contain a ``source.py``.

	Returns:
		list[str]: Lab names in alphabetical order.
	"""

	return sorted(path.parent.name for path in LABS_DIR.glob("*/source.py"))

def lab_label(lab: str) -> str:
	"""Return the display name of a lab.

	Args:
		lab (str): Lab folder name.

	Returns:
		str: ``LABEL`` of the lab's ``source.py``.
	"""

	require_type("lab", lab, str)

	return importlib.import_module(f"models.labs.{lab}.source").LABEL

def lab_home(lab: str) -> str:
	"""Return the home page of a lab, linked from the Labs list.

	A lab can set ``HOME`` in its ``source.py``. Otherwise the home is the site of
	its first source that is not an API, a documentation site or Hugging Face,
	and with none of those, its organization page on Hugging Face.

	Args:
		lab (str): Lab folder name.

	Returns:
		str: URL such as ``https://www.anthropic.com/``.
	"""

	require_type("lab", lab, str)

	module = importlib.import_module(f"models.labs.{lab}.source")

	if getattr(module, "HOME", None):
		return module.HOME

	urls = [urlsplit(source.url) for source in module.SOURCES]

	for url in urls:

		if url.hostname != "huggingface.co" and not url.hostname.startswith(("api.", "api-docs.", "docs.")):
			return f"{url.scheme}://{url.hostname}/"

	authors = [parse_qs(url.query).get("author", [""])[0] for url in urls if url.hostname == "huggingface.co"]

	return f"https://huggingface.co/{authors[0]}" if authors and authors[0] else f"{urls[0].scheme}://{urls[0].hostname}/"

def build_lab(lab: str) -> dict:
	"""Import a lab's ``source.py`` and run its sources with its ``LABEL``.

	Args:
		lab (str): Lab folder name.

	Returns:
		dict: Document from ``run_lab``.
	"""

	require_type("lab", lab, str)

	module = importlib.import_module(f"models.labs.{lab}.source")

	return run_lab(lab, module.LABEL, module.SOURCES)

def summary_entry(document: dict) -> dict:
	"""Return the index entry for one lab document.

	Args:
		document (dict): Document from ``run_lab``.

	Returns:
		dict: Lab slug and label, relative URL of each raw level and of the site file, generation time and per-source status with item counts.
	"""

	require_type("document", document, dict)

	lab = document["slug"]
	sources = [{"rank": s["rank"], "type": s["type"], "status": s["status"], "error": s["error"], "items": len(s["items"])} for s in document["sources"]]
	urls = {level: f"{lab}/raw/{level}.json" for level in LEVELS}

	return {"slug": lab, "label": document["label"], "urls": urls, "site": f"{lab}/site/latest.json", "generated_at": document["generated_at"], "sources": sources}

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
		list[dict]: Index entries, one per built lab.
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
		lab_dir = models_dir / document["slug"]

		for level in LEVELS:
			write_json(lab_dir / "raw" / f"{level}.json", to_json(at_document_level(document, level)))

		if DEFAULT_LEVEL:
			write_json(lab_dir / "index.json", to_json(at_document_level(document, DEFAULT_LEVEL)))

	entries = [dict(summary_entry(document), home=lab_home(document["slug"])) for document in documents]
	untracked = [{"slug": lab, "label": lab_label(lab), "home": lab_home(lab)} for lab in discover_labs() if lab not in TRACKED]

	write_json(models_dir / "index.json", to_json({"generated_at": utc_now(), "labs": entries, "untracked": untracked}))

	return entries

def main() -> None:
	"""Parse the command line, build the site and print one status line per lab."""

	parser = argparse.ArgumentParser(description="Build the GitHub Pages output for the model labs.")
	parser.add_argument("--out", type=Path, default=Path("_site"), help="output folder (site root)")
	parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS, help="labs fetched in parallel")
	parser.add_argument("--only", default="", help="comma-separated lab names; default is every followed lab")
	parser.add_argument("--deep", action="store_true", help="read every page and skip the byte budget, for a history backfill")
	args = parser.parse_args()

	if args.deep:
		os.environ[DEEP_ENV] = "1"

	labs = [name.strip() for name in args.only.split(",") if name.strip()] or [lab for lab in discover_labs() if lab in TRACKED]
	entries = build(args.out, labs, args.workers)

	sys.stdout.reconfigure(encoding="utf-8")

	for entry in entries:
		marks = " ".join(f"{s['rank']}:{s['type']}:{s['status']}:{s['items']}" + (f" ({s['error']})" if s["error"] else "") for s in entry["sources"])
		print(f"{entry['slug']:16} {marks}")

if __name__ == "__main__":
	main()
