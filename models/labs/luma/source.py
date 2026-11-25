"""Sources for Luma AI video and image model releases.

The news page mixes a few announcements (categories Product, Company and
Engineering) with hundreds of how-to articles and model comparisons (category
Guides). The Guides cards are removed before the list is read, otherwise they
fill the size budget and push the model announcements out. The API changelog is
stale (last entry about two years old) and is not used.
"""

from selectolax.lexbor import LexborHTMLParser

from models.common.pages import link_list, node_text
from models.common.runner import cli
from models.common.sources import html
from models.common.validation import require_type

SKIPPED_CATEGORY = "Guides"

_read_cards = link_list(r"^/news/[^/]+$")

def extract_news(page_html: str, source_url: str) -> list[dict]:
	"""Read the news cards, leaving out the cards of the Guides category.

	Args:
		page_html (str): Page HTML.
		source_url (str): Page URL, used to resolve relative links.

	Returns:
		list[dict]: One item per announcement, newest first.
	"""

	require_type("page_html", page_html, str)

	tree = LexborHTMLParser(page_html)

	for label in tree.css("span.typo-label"):

		if node_text(label) != SKIPPED_CATEGORY:
			continue

		card = label.parent

		while card is not None and card.css_first("a.card-link") is None:
			card = card.parent

		if card is not None:
			card.decompose()

	return _read_cards(tree.html, source_url)

LABEL = "Luma AI"

SOURCES = [
	html("https://lumalabs.ai/news", extract_news),
]

if __name__ == "__main__":
	cli(__file__, LABEL, SOURCES)
