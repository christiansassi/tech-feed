"""Run the sources of one lab and build its published JSON documents.

Each source is fetched in priority order and its content is mapped to items in
the common schema. When a source's ``medium`` level exceeds 50 KB, its oldest
items are dropped and the count is recorded in ``items_dropped``. In deep mode
(``models.build --deep``) the budget is lifted and paginated sources are read
page by page until a page adds nothing new. A failing
source is recorded with its error and does not stop the others, so a lab is
always published with whatever could be fetched. The same run is written at
three levels: ``light``, ``medium`` and ``full``.
"""

import dataclasses
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any

from models.common.fetchers import DEFAULT_FETCHERS
from models.common.http import FetchError, new_client
from models.common.items import LEVELS, at_level, newest_first
from models.common.sources import Source, deep_mode
from models.common.validation import require_choice, require_text, require_type

SOURCE_BUDGET_BYTES = 50 * 1024

# Upper bound on the pages read from one source in deep mode.
MAX_PAGES = 100

def utc_now() -> int:
	"""Return the current time as a Unix timestamp in seconds.

	Returns:
		int: Seconds since 1970-01-01 UTC, such as ``1795600800``.
	"""

	return int(dt.datetime.now(dt.timezone.utc).timestamp())

def within_budget(items: list[dict], budget: int = SOURCE_BUDGET_BYTES) -> tuple[list[dict], int]:
	"""Keep the newest items whose ``medium`` level fits in the byte budget.

	Items are expected newest first, so the oldest ones are dropped. The same
	items are kept at every level, so ``full`` can still exceed the budget
	because of the article bodies.

	Args:
		items (list[dict]): Items in the common schema, newest first.
		budget (int): Maximum size in bytes of the source's items at the ``medium`` level.

	Returns:
		tuple[list[dict], int]: Kept items and the number of items dropped.
	"""

	require_type("items", items, list)
	require_type("budget", budget, int)

	kept = len(items)

	while kept > 0 and len(to_json({"items": at_level(items[:kept], "medium")}).encode("utf-8")) > budget:
		kept -= max(1, kept // 10)

	return items[:kept], len(items) - kept

def read_pages(client: Any, source: Source, items: list[dict]) -> list[dict]:
	"""Read the following pages of a paginated source and add their new items.

	Pages are requested from 2 up to ``MAX_PAGES`` and the loop stops at the
	first page that fails or adds no item that was not already seen.

	Args:
		client (Any): primp client shared by the sources of the lab.
		source (Source): Source with a ``next_page`` function.
		items (list[dict]): Items of the first page.

	Returns:
		list[dict]: Items of every page read, newest first.
	"""

	require_type("source", source, Source)
	require_type("items", items, list)

	fetch = source.fetch or DEFAULT_FETCHERS[source.kind]
	seen = {(entry["title"], entry["date"], entry["url"]) for entry in items}
	items = list(items)

	for number in range(2, MAX_PAGES + 1):
		page = dataclasses.replace(source, **source.next_page(number))

		try:
			found = page.extract(fetch(client, page), page.url)
		except Exception:
			break

		new = [entry for entry in found if (entry["title"], entry["date"], entry["url"]) not in seen]

		if not new:
			break

		seen.update((entry["title"], entry["date"], entry["url"]) for entry in new)
		items.extend(new)

	return newest_first(items)

def run_source(client: Any, source: Source, rank: int) -> dict:
	"""Fetch one source, extract its items and return its entry for the published document.

	Args:
		client (Any): primp client shared by the sources of the lab.
		source (Source): Source to fetch.
		rank (int): Priority of the source, 1 for the main one.

	Returns:
		dict: Entry with rank, kind, URL, fetch time, status, HTTP status, error and items at the ``full`` level.
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
		"items_dropped": 0,
		"items": [],
	}

	fetch = source.fetch or DEFAULT_FETCHERS[source.kind]

	try:
		content = fetch(client, source)
		items = source.extract(content, source.url)

		if deep_mode():
			entry["items"] = read_pages(client, source, items) if source.next_page else items
		else:
			entry["items"], entry["items_dropped"] = within_budget(items)
	except FetchError as exc:
		entry.update(status="error", http_status=exc.http_status, error=str(exc))
	except Exception as exc:
		entry.update(status="error", http_status=None, error=f"{type(exc).__name__}: {exc}")

	return entry

def run_lab(slug: str, label: str, sources: list[Source]) -> dict:
	"""Fetch every source of a lab and return the document at the ``full`` level.

	Args:
		slug (str): Lab folder name, e.g. ``"openai"``.
		label (str): Lab name for display, e.g. ``"OpenAI"``.
		sources (list[Source]): Sources in priority order, main source first.

	Returns:
		dict: Document with the lab slug and label, generation time and one entry per source.
	"""

	require_text("slug", slug)
	require_text("label", label)
	require_type("sources", sources, list)

	if not sources:
		raise ValueError("sources must not be empty")

	client = new_client()
	entries = [run_source(client, source, rank) for rank, source in enumerate(sources, start=1)]

	return {"slug": slug, "label": label, "level": "full", "generated_at": utc_now(), "sources": entries}

def at_document_level(document: dict, level: str) -> dict:
	"""Return a copy of a lab document whose items keep only the keys of a level.

	Args:
		document (dict): Document from ``run_lab``.
		level (str): ``"light"``, ``"medium"`` or ``"full"``.

	Returns:
		dict: Document for that level.
	"""

	require_type("document", document, dict)
	require_choice("level", level, LEVELS)

	sources = [dict(entry, items=at_level(entry["items"], level)) for entry in document["sources"]]

	return dict(document, level=level, sources=sources)

def to_json(document: dict) -> str:
	"""Serialize a document as tab-indented JSON.

	Args:
		document (dict): Any JSON-serializable document.

	Returns:
		str: JSON text indented with tabs.
	"""

	require_type("document", document, dict)

	return json.dumps(document, indent="\t", ensure_ascii=False)

def cli(source_file: str, label: str, sources: list[Source]) -> None:
	"""Run a lab from its ``source.py`` and print the document to stdout.

	The level defaults to ``medium``; pass ``light`` or ``full`` as the first command-line argument to change it.

	Args:
		source_file (str): ``__file__`` of the lab's ``source.py``; its folder name is the lab slug.
		label (str): Lab name for display.
		sources (list[Source]): Sources in priority order.

	Returns:
		None
	"""

	require_text("source_file", source_file)

	level = sys.argv[1] if len(sys.argv) > 1 else "medium"
	require_choice("level", level, LEVELS)

	sys.stdout.reconfigure(encoding="utf-8")

	print(to_json(at_document_level(run_lab(Path(source_file).parent.name, label, sources), level)))
