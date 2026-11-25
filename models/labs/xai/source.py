"""Sources for xAI (Grok) model releases.

The news page is a server-rendered list of dated cards. The API release notes
group entries under month headings without a year ("November"); each entry has
a day label ("November 19"), an ``h3`` title and a paragraph. The year is
inferred: it starts at the current year and goes back by one whenever the months,
read from newest to oldest, wrap around.
"""

import datetime as dt
import re

from selectolax.lexbor import LexborHTMLParser

from models.common.items import item, newest_first
from models.common.pages import link_list, node_text
from models.common.runner import cli
from models.common.sources import html
from models.common.validation import require_type

MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]

DAY = re.compile(r"^(January|February|March|April|May|June|July|August|September|October|November|December) (\d{1,2})$")

def extract_release_notes(page_html: str, source_url: str) -> list[dict]:
	"""Read the entries of the xAI API release notes.

	Args:
		page_html (str): Page HTML.
		source_url (str): Page URL, used for anchor links.

	Returns:
		list[dict]: One item per entry, newest first.
	"""

	require_type("page_html", page_html, str)

	today = dt.date.today()
	year = today.year
	previous_month = today.month
	items = []

	for heading in LexborHTMLParser(page_html).css("h3"):
		block = heading.parent.parent if heading.parent is not None else None
		label = block.prev if block is not None else None
		day = DAY.match(node_text(label)) if label is not None else None

		if not day:
			continue

		month = MONTHS.index(day.group(1).lower()) + 1

		if month > previous_month:
			year -= 1

		previous_month = month
		anchor = heading.attributes.get("id")
		url = f"{source_url}#{anchor}" if anchor else source_url
		items.append(item(node_text(heading), f"{year}-{month:02d}-{int(day.group(2)):02d}", url, node_text(block.css_first("p")) or None))

	return newest_first(items)

SOURCES = [
	html("https://x.ai/news", link_list(r"^/news/[^/]+$")),
	html("https://docs.x.ai/docs/release-notes", extract_release_notes),
]

if __name__ == "__main__":
	cli(__file__, SOURCES)
