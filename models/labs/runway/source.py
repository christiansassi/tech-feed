"""Sources for Runway video model releases.

The research page shows undated cards (title and description) for each model.
The changelog lists entries as plain blocks: a date ("Nov 20, 2026") followed by
a block holding a label, the title and the description.
"""

from selectolax.lexbor import LexborHTMLParser

from models.common.items import item, newest_first
from models.common.pages import find_date, link_list, node_text
from models.common.runner import cli
from models.common.sources import hf, html
from models.common.validation import require_type

def extract_changelog(page_html: str, source_url: str) -> list[dict]:
	"""Read the changelog entries that follow a date block.

	Args:
		page_html (str): Page HTML.
		source_url (str): Page URL, used for links.

	Returns:
		list[dict]: One item per entry, newest first.
	"""

	require_type("page_html", page_html, str)

	items = []

	for node in LexborHTMLParser(page_html).css("div"):
		text = node_text(node)
		date = find_date(text)

		if not date or len(text) > 20 or node.next is None:
			continue

		parts = [node_text(child) for child in node.next.iter() if node_text(child)]

		if len(parts) < 2:
			continue

		title, summary = (parts[1], parts[2] if len(parts) > 2 else None) if len(parts) > 2 else (parts[0], parts[1])
		items.append(item(title, date, source_url, summary))

	return newest_first(items)

LABEL = "Runway"

SOURCES = [
	html("https://runway.com/research", link_list(r"^/research/(?!publications$)[^/]+$")),
	html("https://runway.com/changelog", extract_changelog),
	hf("runwayml"),
]

if __name__ == "__main__":
	cli(__file__, LABEL, SOURCES)
