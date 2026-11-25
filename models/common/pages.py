"""Reusable extractors for HTML sources.

Three page shapes cover most labs:

- ``link_list``: a listing page with one card per article. Every link whose path
  matches a pattern is an article; its title, date and introduction are read from
  the card that contains the link.
- ``dated_sections``: a changelog page where each date heading starts an entry.
  Every heading that contains a date becomes an item, with the following content
  as summary and body.
- ``markdown_entries``: a markdown changelog with date headings and one bullet per
  change; every bullet becomes an item.

Each returns an ``extract(page_text, source_url)`` function for ``sources.html``.
"""

import datetime as dt
import re
from collections.abc import Callable
from urllib.parse import urljoin, urlparse

from selectolax.lexbor import LexborHTMLParser, LexborNode

from models.common.items import item, newest_first, to_markdown
from models.common.validation import require_text, require_type

MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec"

DATE_PATTERNS = [
	re.compile(r"\b(\d{4})[-./](\d{1,2})[-./](\d{1,2})\b"),
	re.compile(rf"\b({MONTHS})\.? (\d{{1,2}})(?:st|nd|rd|th)?,? (\d{{4}})\b", re.IGNORECASE),
	re.compile(rf"\b(\d{{1,2}})(?:st|nd|rd|th)? ({MONTHS}),? (\d{{4}})\b", re.IGNORECASE),
	re.compile(r"(\d{4})年(\d{1,2})月(\d{1,2})日"),
]

CARD_TAGS = ("article", "li", "section")

READ_PREFIX = re.compile(r"^(?:read|view|open)(?: (?:the )?(?:full )?(?:article|blog post|post|story|more))?:?\s+", re.IGNORECASE)

def find_date(text: str | None) -> str | None:
	"""Return the first date found in a piece of text as ``YYYY-MM-DD``.

	Recognizes ``2026-11-09``, ``2026.11.09``, ``2026/11/09``, ``Nov 9, 2026``,
	``November 9th, 2026``, ``9 Nov 2026`` and ``2026年11月9日``.

	Args:
		text (str | None): Text to search.

	Returns:
		str | None: Date as ``YYYY-MM-DD``, or None when no date is found.
	"""

	if not text:
		return None

	require_type("text", text, str)

	for index, pattern in enumerate(DATE_PATTERNS):
		match = pattern.search(text)

		if not match:
			continue

		groups = match.groups()

		try:
			if index in (0, 3):
				day = dt.date(int(groups[0]), int(groups[1]), int(groups[2]))
			elif index == 1:
				day = dt.datetime.strptime(f"{groups[0][:3]} {groups[1]} {groups[2]}", "%b %d %Y").date()
			else:
				day = dt.datetime.strptime(f"{groups[1][:3]} {groups[0]} {groups[2]}", "%b %d %Y").date()
		except ValueError:
			continue

		return day.isoformat()

	return None

def node_text(node: LexborNode | None) -> str:
	"""Return the visible text of a node on one line.

	Args:
		node (LexborNode | None): HTML node.

	Returns:
		str: Text with whitespace collapsed, or an empty string.
	"""

	if node is None:
		return ""

	return re.sub(r"\s+", " ", node.text(separator=" ", strip=True)).strip()

def _card_of(anchor: LexborNode, pattern: re.Pattern) -> LexborNode:
	"""Return the smallest ancestor of a link that holds only this article.

	Climb from the link while the ancestor still contains a single matching link,
	stopping at a card-like tag or after a few levels.

	Args:
		anchor (LexborNode): Article link.
		pattern (re.Pattern): Pattern that article links match.

	Returns:
		LexborNode: Card node, or the link itself.
	"""

	card = anchor
	node = anchor.parent

	for _ in range(6):

		if node is None or node.tag in ("body", "html", "main"):
			break

		links = {a.attributes.get("href") for a in node.css("a[href]") if pattern.search(urlparse(a.attributes.get("href") or "").path)}

		if len(links) > 1:
			break

		card = node

		if node.tag in CARD_TAGS:
			break

		node = node.parent

	return card

def _title_of(card: LexborNode, anchor: LexborNode, title: str | None = None) -> str:
	"""Return the title of a card.

	When ``title`` is given, use the text of the first element it selects. Otherwise
	try, in order: the link's ``aria-label`` without a leading "Read ...:" phrase,
	the first heading inside the card, the first image ``alt`` text, the first
	title-like element, the first paragraph, and finally the link text.

	Args:
		card (LexborNode): Card node.
		anchor (LexborNode): Article link inside the card.
		title (str | None): CSS selector of the title element, for pages where the default order picks the wrong text.

	Returns:
		str: Title text.
	"""

	if title is not None:
		return node_text(card.css_first(title))

	label = READ_PREFIX.sub("", anchor.attributes.get("aria-label") or "").strip()

	if len(label) > 3:
		return label

	for selector in ("h1, h2, h3, h4, h5, h6", "img[alt]", "[class*=title], [class*=Title]", "p"):
		node = card.css_first(selector)
		text = (node.attributes.get("alt") or "").strip() if node is not None and node.tag == "img" else node_text(node)

		if len(text) > 3:
			return text

	return node_text(anchor)

def _summary_of(card: LexborNode, title: str) -> str | None:
	"""Return the first paragraph of a card that is not the title.

	Args:
		card (LexborNode): Card node.
		title (str): Card title, skipped if a paragraph repeats it.

	Returns:
		str | None: Paragraph text, or None.
	"""

	for paragraph in card.css("p, [class*=desc], [class*=excerpt], [class*=summary]"):
		text = node_text(paragraph)

		if len(text) > 30 and title not in text[: len(title) + 20] and find_date(text) != text:
			return text

	return None

def _merge(current: dict, candidate: dict) -> dict:
	"""Combine two cards for the same article, keeping the best value of each field.

	A page can show one article twice, for example a dated row with a "Read Paper"
	button and an undated card with the real title.

	Args:
		current (dict): Item kept so far.
		candidate (dict): Item read from the later card.

	Returns:
		dict: Item with the first date found, a real title in place of a short label, and the longer summary.
	"""

	title = current["title"]

	if len(title or "") < 15 <= len(candidate["title"] or ""):
		title = candidate["title"]

	summary = max(current["summary"], candidate["summary"], key=lambda text: len(text or ""))

	return dict(current, title=title, date=current["date"] or candidate["date"], summary=summary)

def link_list(pattern: str, date_from_url: Callable[[str], str | None] | None = None, scope: str | None = None, title: str | None = None) -> Callable[[str, str], list[dict]]:
	"""Return an extractor for a listing page whose article links match ``pattern``.

	Args:
		pattern (str): Regular expression that the path of article links on the same host matches, e.g. ``r"^/news/[^/]+$"``.
		date_from_url (Callable | None): Optional function that reads the date from an article URL, for pages that show no dates.
		scope (str | None): Optional CSS selector of the page area that holds the list, e.g. a sidebar; links elsewhere are ignored.
		title (str | None): Optional CSS selector of the title element inside each card, e.g. ``"[class*=blogTitle]"``.

	Returns:
		Callable[[str, str], list[dict]]: Extractor ``extract(page_html, source_url)``.
	"""

	require_text("pattern", pattern)

	if scope is not None:
		require_text("scope", scope)

	if title is not None:
		require_text("title", title)

	compiled = re.compile(pattern)

	def extract(page_html: str, source_url: str) -> list[dict]:
		"""Read the article cards of a listing page.

		Args:
			page_html (str): Page HTML.
			source_url (str): Page URL, used to resolve relative links.

		Returns:
			list[dict]: One item per article, newest first.
		"""

		require_type("page_html", page_html, str)

		tree = LexborHTMLParser(page_html)
		host = urlparse(source_url).netloc
		seen = {}

		anchors = [a for area in tree.css(scope) for a in area.css("a[href]")] if scope else tree.css("a[href]")

		for anchor in anchors:
			href = anchor.attributes.get("href") or ""
			url = urljoin(source_url, href).split("#")[0]

			if href.startswith("#") or urlparse(url).netloc != host or not compiled.search(urlparse(url).path):
				continue

			card = _card_of(anchor, compiled)
			card_title = _title_of(card, anchor, title)

			if not card_title:
				continue

			time_node = card.css_first("time[datetime]")
			date = (time_node.attributes.get("datetime") if time_node else None) or find_date(node_text(card)) or (date_from_url(url) if date_from_url else None)
			candidate = item(card_title, date, url, _summary_of(card, card_title))

			seen[url] = _merge(seen[url], candidate) if url in seen else candidate

		return newest_first(list(seen.values()))

	return extract

def dated_sections(heading: str = "h1, h2, h3, h4") -> Callable[[str, str], list[dict]]:
	"""Return an extractor for a changelog page where date headings start each entry.

	The page is walked in document order; every heading that matches ``heading``
	and contains a date opens a new entry, and the content up to the next such
	heading becomes the entry's summary and body. The entry title is the first
	line of the entry that is not the date itself.

	Args:
		heading (str): CSS selector for the headings that may carry dates.

	Returns:
		Callable[[str, str], list[dict]]: Extractor ``extract(page_html, source_url)``.
	"""

	require_text("heading", heading)

	def extract(page_html: str, source_url: str) -> list[dict]:
		"""Split a changelog page into dated entries.

		Args:
			page_html (str): Page HTML.
			source_url (str): Page URL, used for links and anchors.

		Returns:
			list[dict]: One item per dated entry, newest first.
		"""

		require_type("page_html", page_html, str)

		tree = LexborHTMLParser(page_html)

		for junk in tree.css("script, style, nav, header, footer, svg, noscript"):
			junk.decompose()

		root = tree.css_first("main") or tree.body
		headings = {node.mem_id for node in root.css(heading)}
		entries = []

		for node in root.traverse():

			if node.mem_id in headings and find_date(node_text(node)):
				anchor = node.attributes.get("id")
				entries.append({"date": find_date(node_text(node)), "date_text": node_text(node), "url": f"{source_url}#{anchor}" if anchor else source_url, "parts": []})
				continue

			if entries and node.tag in ("p", "li", "h1", "h2", "h3", "h4", "h5", "pre", "blockquote", "table") and not any(parent.tag in ("p", "li", "pre", "blockquote", "table") for parent in _parents(node)):
				entries[-1]["parts"].append(node.html)

		items = []

		for entry in entries:
			body = to_markdown("\n".join(entry["parts"]), source_url)
			lines = [line.strip("#*- ").strip() for line in (body or "").splitlines() if line.strip()]
			lines = [clean_title(line) for line in lines]
			title = next((line for line in lines if line and line != entry["date_text"]), entry["date_text"])
			items.append(item(title[:200], entry["date"], entry["url"], clean_title(body or "") or None, body))

		return newest_first(items)

	return extract

def markdown_entries(page_url: str) -> Callable[[str, str], list[dict]]:
	"""Return an extractor for a markdown changelog with date headings and one bullet per change.

	Each ``#`` heading that contains a date starts a day; each top-level bullet
	under it becomes one item. The bullet's leading bold text is the title, the
	whole bullet is the summary and body, and the link points to the day's anchor
	on the HTML page (taken from a ``{% id="..." %}`` marker when present).

	Args:
		page_url (str): URL of the human-readable page, used for links.

	Returns:
		Callable[[str, str], list[dict]]: Extractor ``extract(markdown_text, source_url)``.
	"""

	require_text("page_url", page_url)

	def extract(markdown_text: str, source_url: str) -> list[dict]:
		"""Split a markdown changelog into one item per bullet.

		Args:
			markdown_text (str): Markdown document.
			source_url (str): URL the markdown was fetched from (unused).

		Returns:
			list[dict]: One item per change, newest first.
		"""

		require_type("markdown_text", markdown_text, str)

		bullets = []
		date = None
		anchor = None

		for line in markdown_text.splitlines():

			if line.startswith("#") and find_date(line):
				date = find_date(line)
				marker = re.search(r'id="([^"]+)"', line)
				anchor = marker.group(1) if marker else None
				continue

			if date and re.match(r"^[*-]\s+", line):
				bullets.append({"date": date, "anchor": anchor, "lines": [re.sub(r"^[*-]\s+", "", line)]})
			elif date and bullets and line.startswith((" ", "\t")) and line.strip():
				bullets[-1]["lines"].append(line.strip())

		items = []

		for bullet in bullets:
			text = " ".join(bullet["lines"])
			bold = re.match(r"\*\*(.+?)\*\*", text)
			title = clean_title(bold.group(1) if bold else text[:120])
			url = f"{page_url}#{bullet['anchor']}" if bullet["anchor"] else page_url
			body = re.sub(r"\]\((/[^)]*)\)", lambda m: f"]({urljoin(page_url, m.group(1))})", text)
			items.append(item(title, bullet["date"], url, clean_title(body), body))

		return newest_first(items)

	return extract

def clean_title(line: str) -> str:
	"""Turn markdown into one line of plain text: keep link texts, drop anchors, images, emphasis marks and zero-width characters.

	Args:
		line (str): One line of markdown.

	Returns:
		str: Plain text.
	"""

	require_type("line", line, str)

	line = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", line)
	line = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", line)
	line = line.replace("\u200b", "").replace("`", "").replace("**", "").replace("__", "")

	return re.sub(r"\s+", " ", line).strip(" #*-:")

def _parents(node: LexborNode) -> list[LexborNode]:
	"""Return the ancestors of a node, nearest first.

	Args:
		node (LexborNode): HTML node.

	Returns:
		list[LexborNode]: Ancestors up to the document root.
	"""

	parents = []
	parent = node.parent

	while parent is not None:
		parents.append(parent)
		parent = parent.parent

	return parents
