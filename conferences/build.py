"""Fetch the page of every tracked conference and publish it as raw text.

For each conference in ``conferences/sources.py``, download its page, turn the
HTML into plain text (keeping JSON-LD blocks, which often carry the dates), find
the link to its ticket shop and download that page too, then write
``<out>/conferences/<slug>/raw/page.json``. ``<out>/conferences/index.json``
lists every conference with its raw file, its site file
(``<slug>/site/latest.json``, written by the Raspberry updater) and the fetch
status. Dates, place and ticket status are read from this text later by Codex.

Usage: ``python -m conferences.build [--out _site] [--workers 8]``
"""

import argparse
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urljoin, urlparse

from selectolax.lexbor import LexborHTMLParser

from conferences.sources import CONFERENCES, Conference
from models.common.http import FetchError, new_client, send
from models.common.runner import to_json, utc_now
from models.common.validation import require_positive_number, require_text, require_type

DEFAULT_WORKERS = 8

TEXT_CHARS = 60000

DROPPED_TAGS = "script, style, noscript, svg, template, iframe"

TICKET_PLATFORMS = ("pretix", "ti.to", "tito.io", "eventbrite", "billetweb", "weezevent", "helloasso", "tickettailor", "universe.com", "lu.ma", "eventim", "yesticket", "tickets.")

TICKET_WORDS = re.compile(r"ticket|billet|biglietti|entradas|registr|inscri|anmeld|buy", re.IGNORECASE)

def page_text(body: str) -> str:
	"""Turn a fetched page into plain text, one block per line.

	HTML loses its tags, scripts and styles, but JSON-LD blocks are kept at the
	end because many sites put the event dates there. Other formats (Markdown,
	YAML, calendar feeds) are returned as they are.

	Args:
		body (str): Response body.

	Returns:
		str: Text with collapsed spaces and no empty or repeated lines.
	"""

	require_type("body", body, str)

	if "<html" not in body[:2000].lower() and "<body" not in body.lower():
		return body.strip()

	tree = LexborHTMLParser(body)
	structured = [node.text() for node in tree.css('script[type="application/ld+json"]')]

	for node in tree.css(DROPPED_TAGS):
		node.decompose()

	root = tree.body or tree.root
	lines = [re.sub(r"\s+", " ", line).strip() for line in (root.text(separator="\n") if root else "").split("\n")]
	kept = []

	for line in lines:

		if line and (not kept or kept[-1] != line):
			kept.append(line)

	return "\n".join(kept + [block.strip() for block in structured if block.strip()])

def ticket_link(body: str, page_url: str) -> str | None:
	"""Find the most likely ticket link on a page, ignoring CTF links.

	Links to known ticket platforms rank first, then links whose text or address
	mentions tickets or registration in English, French, Italian, Spanish or German.

	Args:
		body (str): HTML of the page.
		page_url (str): Final URL of the page, used to resolve relative links.

	Returns:
		str | None: Absolute URL of the ticket page, or None when there is no such link.
	"""

	require_type("body", body, str)
	require_text("page_url", page_url)

	best, best_score = None, 0

	for anchor in LexborHTMLParser(body).css("a[href]"):
		href = urljoin(page_url, anchor.attributes.get("href") or "").split("#")[0]
		text = anchor.text(strip=True)
		haystack = f"{href} {text}".lower()

		if not href.startswith("http") or href.rstrip("/") == page_url.rstrip("/") or "ctf" in haystack:
			continue

		host = urlparse(href).netloc.lower()
		score = 2 if any(platform in host for platform in TICKET_PLATFORMS) else 1 if TICKET_WORDS.search(haystack) else 0

		if score > best_score:
			best, best_score = href, score

	return best

def clip(text: str) -> tuple[str, bool]:
	"""Cut a text to ``TEXT_CHARS`` characters.

	Args:
		text (str): Page text.

	Returns:
		tuple[str, bool]: The text, and whether it was cut.
	"""

	require_type("text", text, str)

	return text[:TEXT_CHARS], len(text) > TEXT_CHARS

def fetch_conference(conference: Conference) -> dict:
	"""Download the page and the ticket page of one conference.

	Args:
		conference (Conference): Conference to fetch.

	Returns:
		dict: Raw document with the page text, the ticket page text and the fetch status.
	"""

	require_type("conference", conference, Conference)

	client = new_client()
	document = {"slug": conference.slug, "label": conference.label, "note": conference.note, "fetched_at": utc_now(), "status": "ok", "error": None, "page": None, "tickets": None}

	try:
		response = send(client, conference.url)
	except FetchError as error:
		document.update(status="error", error=str(error))
		return document

	body = response.text
	final_url = str(response.url)
	text, truncated = clip(page_text(body))
	document["page"] = {"url": conference.url, "final_url": final_url, "text": text, "truncated": truncated}

	tickets_url = conference.tickets or (ticket_link(body, final_url) if "<a" in body else None)

	if tickets_url:

		try:
			tickets_text, tickets_truncated = clip(page_text(send(client, tickets_url).text))
			document["tickets"] = {"url": tickets_url, "text": tickets_text, "truncated": tickets_truncated, "error": None}
		except FetchError as error:
			document["tickets"] = {"url": tickets_url, "text": None, "truncated": False, "error": str(error)}

	return document

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

def build(out_dir: Path, workers: int) -> list[dict]:
	"""Fetch every conference in parallel and write the raw files and the index.

	Args:
		out_dir (Path): Site root, such as ``_site``.
		workers (int): Maximum number of conferences fetched at the same time.

	Returns:
		list[dict]: Index entries, one per conference.
	"""

	require_type("out_dir", out_dir, Path)
	require_type("workers", workers, int)
	require_positive_number("workers", workers)

	with ThreadPoolExecutor(max_workers=min(workers, os.cpu_count() or 1)) as pool:
		documents = list(pool.map(fetch_conference, CONFERENCES))

	root = out_dir / "conferences"
	entries = []

	for document in documents:
		slug = document["slug"]
		write_json(root / slug / "raw" / "page.json", to_json(document))
		entries.append({"slug": slug, "label": document["label"], "raw": f"{slug}/raw/page.json", "site": f"{slug}/site/latest.json", "status": document["status"], "error": document["error"], "tickets": (document["tickets"] or {}).get("url")})

	write_json(root / "index.json", to_json({"generated_at": utc_now(), "conferences": entries}))

	return entries

def main() -> None:
	"""Parse the command line, build the conference files and print one status line per conference."""

	parser = argparse.ArgumentParser(description="Fetch the tracked conference pages for the site.")
	parser.add_argument("--out", type=Path, default=Path("_site"), help="output folder (site root)")
	parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS, help="conferences fetched in parallel")
	args = parser.parse_args()

	entries = build(args.out, args.workers)

	sys.stdout.reconfigure(encoding="utf-8")

	for entry in entries:
		print(f"{entry['slug']:26} {entry['status']:6} tickets={entry['tickets'] or '-'}" + (f" ({entry['error']})" if entry["error"] else ""))

if __name__ == "__main__":
	main()
