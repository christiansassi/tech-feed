"""Sources for OpenAI model releases: the news feed and the API changelog, which lists model ids.

The changelog groups entries under month headings ("November, 2026"); each entry
has a day badge ("Nov 24"), type and model badges ("Update", "chat-latest") and
a paragraph. The year comes from the month heading.
"""

import re

from selectolax.lexbor import LexborHTMLParser

from models.common.items import item, newest_first, to_markdown
from models.common.pages import find_date, node_text
from models.common.runner import cli
from models.common.sources import hf, html, rss
from models.common.validation import require_type

DAY = re.compile(r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* (\d{1,2})$")

def extract_changelog(page_html: str, source_url: str) -> list[dict]:
	"""Read the dated entries of the OpenAI API changelog.

	Args:
		page_html (str): Page HTML.
		source_url (str): Page URL, used for links.

	Returns:
		list[dict]: One item per entry, titled by its badges (e.g. "Update: chat-latest"), newest first.
	"""

	require_type("page_html", page_html, str)

	tree = LexborHTMLParser(page_html)
	year = None
	items = []

	for node in tree.root.traverse():

		if node.tag == "h3":
			month = re.search(r"(\d{4})", node_text(node))
			year = month.group(1) if month else year
			continue

		day = DAY.match(node_text(node)) if node.attributes.get("data-variant") == "outline" else None

		if not day or not year:
			continue

		entry = node.parent.parent if node.parent is not None else None

		if entry is None:
			continue

		badges = [node_text(badge) for badge in entry.css('[data-variant="soft"]')]
		paragraphs = entry.css("p")
		text = " ".join(node_text(p) for p in paragraphs)
		title = f"{badges[0]}: {', '.join(badges[1:])}" if len(badges) > 1 else (badges[0] if badges else text[:120])
		body = to_markdown("".join(p.html for p in paragraphs), source_url)
		items.append(item(title, find_date(f"{day.group(1)} {day.group(2)}, {year}"), source_url, text, body))

	return newest_first(items)

LABEL = "OpenAI"

SOURCES = [
	rss("https://openai.com/news/rss.xml"),
	html("https://developers.openai.com/api/docs/changelog", extract_changelog),
	hf("openai"),
]

if __name__ == "__main__":
	cli(__file__, LABEL, SOURCES)
