"""Sources for Nous Research (Hermes) model releases.

The releases page lists one ``article.nw-release-row`` per release, with a
``MM/DD/YY`` date, a type (MODEL, AGENT or PAPER), a title linking to the model
or paper, and a one-line description.
"""

import re

from selectolax.lexbor import LexborHTMLParser

from models.common.items import item, newest_first
from models.common.pages import node_text
from models.common.runner import cli
from models.common.sources import hf, html
from models.common.validation import require_type

def extract_releases(page_html: str, source_url: str) -> list[dict]:
	"""Read the release rows of the Nous releases page.

	Args:
		page_html (str): Page HTML.
		source_url (str): Page URL (unused).

	Returns:
		list[dict]: One item per release, titled "TYPE: name", newest first.
	"""

	require_type("page_html", page_html, str)

	items = []

	for row in LexborHTMLParser(page_html).css("article.nw-release-row"):
		link = row.css_first(".nw-catalogue-row-title a")
		kind = node_text(row.css_first(".nw-release-type"))
		raw_date = re.fullmatch(r"(\d{2})/(\d{2})/(\d{2})", node_text(row.css_first(".nw-release-date")))
		date = f"20{raw_date.group(3)}-{raw_date.group(1)}-{raw_date.group(2)}" if raw_date else None
		title = f"{kind}: {node_text(link)}" if kind else node_text(link)
		url = link.attributes.get("href") if link is not None else None
		items.append(item(title, date, url, node_text(row.css_first(".nw-catalogue-description")) or None))

	return newest_first(items)

LABEL = "Nous Research"

SOURCES = [
	html("https://nousresearch.com/releases", extract_releases),
	hf("NousResearch"),
]

if __name__ == "__main__":
	cli(__file__, LABEL, SOURCES)
