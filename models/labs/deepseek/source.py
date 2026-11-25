"""Sources for DeepSeek model releases.

The API docs have no news index page: each release lives at /news/newsYYMMDD/
and every news page lists all releases in its sidebar. The newest news page is
found through the docs sitemap and converted to markdown.
"""

import re

import primp

from models.common.fetchers import fetch_markdown
from models.common.http import FetchError, send
from models.common.runner import cli
from models.common.sources import Source, custom, hf, html

SITEMAP = "https://api-docs.deepseek.com/sitemap.xml"

NEWS_URL = re.compile(r"<loc>(https://api-docs\.deepseek\.com/news/news(\d{6})/?)</loc>")


def latest_news(client: primp.Client, source: Source) -> str:
	"""Return the newest DeepSeek news page as markdown.

	Args:
		client (primp.Client): Client from ``new_client``.
		source (Source): Source whose URL is the docs sitemap.

	Returns:
		str: Markdown of the newest news page, including the sidebar with every release.
	"""

	sitemap = send(client, source.url).text
	pages = NEWS_URL.findall(sitemap)

	if not pages:
		raise FetchError("no /news/ pages in the sitemap")

	newest = max(pages, key=lambda page: page[1])[0]

	return fetch_markdown(client, html(newest))


SOURCES = [
	custom("html", SITEMAP, latest_news),
	hf("deepseek-ai"),
	html("https://api-docs.deepseek.com/updates"),
]

if __name__ == "__main__":
	cli(__file__, SOURCES)
