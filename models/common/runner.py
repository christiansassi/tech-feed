"""Run the sources of one lab and build its published JSON document.

Each source is fetched in priority order. A failing source is recorded with its
error and does not stop the others, so a lab is always published with whatever
could be fetched.
"""

import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any

from models.common.fetchers import DEFAULT_FETCHERS
from models.common.http import FetchError, new_client
from models.common.sources import Source
from models.common.validation import require_text, require_type


def utc_now() -> str:
	"""Return the current UTC time as an ISO 8601 string with a ``Z`` suffix.

	Returns:
		str: Timestamp such as ``"2026-11-25T10:00:00Z"``.
	"""

	return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run_source(client: Any, source: Source, rank: int) -> dict:
	"""Fetch one source and return its entry for the published document.

	Args:
		client (Any): primp client shared by the sources of the lab.
		source (Source): Source to fetch.
		rank (int): Priority of the source, 1 for the main one.

	Returns:
		dict: Entry with rank, kind, URL, status, HTTP status, error and content.
	"""

	require_type("source", source, Source)
	require_type("rank", rank, int)

	entry = {
		"rank": rank,
		"type": source.kind,
		"url": source.url,
		"fetched_at": utc_now(),
		"status": "ok",
		"http_status": 200,
		"error": None,
		"content": None,
	}

	fetch = source.fetch or DEFAULT_FETCHERS[source.kind]

	try:
		entry["content"] = fetch(client, source)
	except FetchError as exc:
		entry.update(status="error", http_status=exc.http_status, error=str(exc))
	except Exception as exc:
		entry.update(status="error", http_status=None, error=f"{type(exc).__name__}: {exc}")

	return entry


def run_lab(lab: str, sources: list[Source]) -> dict:
	"""Fetch every source of a lab and return the document published for it.

	Args:
		lab (str): Lab folder name, e.g. ``"qwen"``.
		sources (list[Source]): Sources in priority order, main source first.

	Returns:
		dict: Document with the lab name, generation time and one entry per source.
	"""

	require_text("lab", lab)
	require_type("sources", sources, list)

	if not sources:
		raise ValueError("sources must not be empty")

	client = new_client()
	entries = [run_source(client, source, rank) for rank, source in enumerate(sources, start=1)]

	return {"lab": lab, "generated_at": utc_now(), "sources": entries}


def to_json(document: dict) -> str:
	"""Serialize a lab document as tab-indented JSON.

	Args:
		document (dict): Document from ``run_lab``.

	Returns:
		str: JSON text indented with tabs.
	"""

	require_type("document", document, dict)

	return json.dumps(document, indent="\t", ensure_ascii=False)


def cli(source_file: str, sources: list[Source]) -> None:
	"""Run a lab from its ``source.py`` and print the document to stdout.

	Args:
		source_file (str): ``__file__`` of the lab's ``source.py``; its folder name is the lab name.
		sources (list[Source]): Sources in priority order.

	Returns:
		None
	"""

	require_text("source_file", source_file)

	sys.stdout.reconfigure(encoding="utf-8")

	print(to_json(run_lab(Path(source_file).parent.name, sources)))
