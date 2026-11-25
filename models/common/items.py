"""Common item schema shared by every source, plus the generic extractors.

Every source is reduced to a list of items with the same keys:

- ``title``: name of the release or article, which usually carries the model name
- ``date``: publication time as a Unix timestamp in seconds (midnight UTC when the source gives only the day), or None
- ``url``: absolute link to the article, model page or repository, or None
- ``summary``: short plain-text introduction, or None
- ``body``: full text as markdown when the source provides it, or None

The three published levels keep different keys: ``light`` keeps title, date and
url; ``medium`` adds summary; ``full`` adds body.
"""

import datetime as dt
import email.utils
import html as htmllib
import re
from typing import Any
from urllib.parse import urljoin

from markdownify import markdownify

from models.common.validation import require_choice, require_type

LEVELS = {
	"light": ("title", "date", "url"),
	"medium": ("title", "date", "url", "summary"),
	"full": ("title", "date", "url", "summary", "body"),
}

SUMMARY_CHARS = 600

_TAG = re.compile(r"<[^>]+>")

_SPACE = re.compile(r"\s+")

_PATH_DATE = re.compile(r"/(20\d{2})/(\d{2})/(\d{2})/")

def text_of(value: Any) -> str | None:
	"""Return the text of an xmltodict value, which may be a string, a dict with ``#text`` or a list.

	Args:
		value (Any): Value from an xmltodict tree or a JSON document.

	Returns:
		str | None: The text, or None when there is none.
	"""

	if value is None:
		return None

	if isinstance(value, list):
		return text_of(value[0]) if value else None

	if isinstance(value, dict):
		return text_of(value.get("#text"))

	text = str(value).strip()

	return text or None

def plain_text(markup: str | None) -> str | None:
	"""Strip HTML tags and entities and collapse whitespace.

	Args:
		markup (str | None): HTML or plain text.

	Returns:
		str | None: Plain text on one line, or None when empty.
	"""

	if markup is None:
		return None

	require_type("markup", markup, str)

	text = _SPACE.sub(" ", htmllib.unescape(_TAG.sub(" ", markup))).strip()

	return text or None

def summarize(markup: str | None) -> str | None:
	"""Return a short plain-text introduction from HTML or text.

	Long text is cut at the last word boundary before ``SUMMARY_CHARS`` and ends with an ellipsis.

	Args:
		markup (str | None): HTML or plain text, often a feed description.

	Returns:
		str | None: Introduction of at most about ``SUMMARY_CHARS`` characters, or None.
	"""

	text = plain_text(markup)

	if text is None or len(text) <= SUMMARY_CHARS:
		return text

	return text[:SUMMARY_CHARS].rsplit(" ", 1)[0] + "..."

def to_markdown(markup: str | None, base_url: str | None = None) -> str | None:
	"""Convert an HTML fragment to markdown with absolute links.

	Args:
		markup (str | None): HTML fragment, or text that is returned unchanged when it has no tags.
		base_url (str | None): URL that relative links are resolved against.

	Returns:
		str | None: Markdown text, or None when empty.
	"""

	if markup is None:
		return None

	require_type("markup", markup, str)

	if "<" not in markup:
		return markup.strip() or None

	text = markdownify(markup, heading_style="ATX").strip()

	if base_url:
		text = re.sub(r"\]\((/[^)\s]*)\)", lambda m: f"]({urljoin(base_url, m.group(1))})", text)

	return text or None

def timestamp(value: Any) -> int | None:
	"""Convert a date in any common format to a Unix timestamp in seconds.

	Accepts RFC 2822 (RSS), ISO 8601, ``YYYYMMDD``, ``YYYY/MM/DD``, ``YYYY-MM`` and Unix timestamps in seconds or milliseconds. A date without a time counts as midnight UTC, and a month without a day counts as its first day.

	Args:
		value (Any): Date value as found in the source.

	Returns:
		int | None: Seconds since 1970-01-01 UTC, or None when the value is empty or cannot be parsed.
	"""

	if value is None or value == "":
		return None

	if isinstance(value, (int, float)) and not isinstance(value, bool):
		return int(value / 1000 if value > 10**11 else value)

	text = str(value).strip()

	if re.fullmatch(r"\d{10,13}", text):
		return timestamp(int(text))

	if re.fullmatch(r"\d{8}", text):
		text = f"{text[:4]}-{text[4:6]}-{text[6:]}"

	text = re.sub(r"^(\d{4})[/.](\d{1,2})[/.](\d{1,2})", lambda m: f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}", text)

	if re.fullmatch(r"\d{4}-\d{2}", text):
		text += "-01"

	parsed = None

	try:
		parsed = dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
	except ValueError:

		try:
			parsed = email.utils.parsedate_to_datetime(text)
		except (TypeError, ValueError):
			return None

	if parsed.tzinfo is None:
		parsed = parsed.replace(tzinfo=dt.timezone.utc)

	return int(parsed.timestamp())

def item(title: Any, date: Any = None, url: Any = None, summary: str | None = None, body: str | None = None, base_url: str | None = None) -> dict:
	"""Build one item in the common schema.

	Args:
		title (Any): Release or article title; converted to plain text.
		date (Any): Date in any format accepted by ``timestamp``.
		url (Any): Link to the article; relative links are resolved against ``base_url``.
		summary (str | None): Introduction as HTML or text; shortened by ``summarize``.
		body (str | None): Full text as markdown, or None.
		base_url (str | None): URL of the source, used to resolve a relative ``url``.

	Returns:
		dict: Item with ``title``, ``date``, ``url``, ``summary`` and ``body``.
	"""

	link = text_of(url)

	if link and base_url:
		link = urljoin(base_url, link)

	return {
		"title": plain_text(text_of(title)),
		"date": timestamp(date),
		"url": link,
		"summary": summarize(summary),
		"body": body or None,
	}

def newest_first(items: list[dict]) -> list[dict]:
	"""Sort items by date, newest first, keeping undated items at the end in their original order.

	Args:
		items (list[dict]): Items in the common schema.

	Returns:
		list[dict]: Sorted items.
	"""

	require_type("items", items, list)

	dated = sorted((i for i in items if i["date"]), key=lambda i: i["date"], reverse=True)

	return dated + [i for i in items if not i["date"]]

def at_level(items: list[dict], level: str) -> list[dict]:
	"""Keep only the keys that belong to a level.

	Args:
		items (list[dict]): Items in the common schema.
		level (str): ``"light"``, ``"medium"`` or ``"full"``.

	Returns:
		list[dict]: Items with the keys of the level only.
	"""

	require_type("items", items, list)
	require_choice("level", level, LEVELS)

	keys = LEVELS[level]

	return [{key: entry.get(key) for key in keys} for entry in items]

def _feed_link(entry: dict) -> str | None:
	"""Return the article link of an RSS item or Atom entry.

	Args:
		entry (dict): Item or entry from xmltodict.

	Returns:
		str | None: Link URL, or None.
	"""

	link = entry.get("link")

	if isinstance(link, list):
		alternates = [l for l in link if isinstance(l, dict) and l.get("@rel", "alternate") == "alternate"]
		link = (alternates or link)[0]

	if isinstance(link, dict):
		return link.get("@href") or text_of(link)

	return text_of(link) or text_of(entry.get("guid"))

def extract_feed(content: dict, source_url: str) -> list[dict]:
	"""Turn an xmltodict RSS, RDF or Atom document into items.

	An entry without a date element gets the date from its link when the link
	contains one as ``/YYYY/MM/DD/``.

	Args:
		content (dict): Feed converted by xmltodict.
		source_url (str): Feed URL, used to resolve relative links.

	Returns:
		list[dict]: One item per feed entry, newest first.
	"""

	require_type("content", content, dict)

	if "rss" in content:
		entries = content["rss"].get("channel", {}).get("item", [])
	elif "feed" in content:
		entries = content["feed"].get("entry", [])
	else:
		entries = content.get("rdf:RDF", {}).get("item", [])

	if isinstance(entries, dict):
		entries = [entries]

	items = []

	for entry in entries:
		date = entry.get("pubDate") or entry.get("published") or entry.get("updated") or entry.get("dc:date")
		description = text_of(entry.get("description")) or text_of(entry.get("summary")) or text_of(entry.get("media:description"))
		content_html = text_of(entry.get("content:encoded")) or text_of(entry.get("content"))
		link = _feed_link(entry)

		if not date and link:
			path_date = _PATH_DATE.search(link)
			date = "-".join(path_date.groups()) if path_date else None

		items.append(item(entry.get("title"), text_of(date), link, description or content_html, to_markdown(content_html or description, link or source_url), source_url))

	return newest_first(items)

def extract_hf(content: list, source_url: str) -> list[dict]:
	"""Turn a Hugging Face models API response into items.

	Args:
		content (list): JSON list from ``/api/models``.
		source_url (str): API URL (unused, kept for a uniform signature).

	Returns:
		list[dict]: One item per model with its id as title and its task as summary, newest first.
	"""

	require_type("content", content, list)

	items = []

	for model in content:
		task = model.get("pipeline_tag")
		summary = f"Hugging Face model, task: {task}" if task else "Hugging Face model"
		items.append(item(model.get("id"), model.get("createdAt"), f"https://huggingface.co/{model.get('id')}", summary))

	return newest_first(items)

def extract_github(content: list, source_url: str) -> list[dict]:
	"""Turn a GitHub organization repositories response into items.

	Args:
		content (list): JSON list from ``/orgs/<org>/repos``.
		source_url (str): API URL (unused, kept for a uniform signature).

	Returns:
		list[dict]: One item per repository with its description as summary, newest first.
	"""

	require_type("content", content, list)

	return newest_first([item(repo.get("full_name"), repo.get("created_at"), repo.get("html_url"), repo.get("description")) for repo in content])
