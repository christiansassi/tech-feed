"""Sources for DeepSeek model releases.

The API docs have no news index page: each release lives at /news/newsYYMMDD/
and every news page lists all releases in its sidebar. The newest news page is
found through the docs sitemap and its sidebar is read; each release's date
comes from its URL. The updates page is a changelog with one dated heading per
change.
"""

import re

import primp

from models.common.fetchers import fetch_html
from models.common.http import FetchError, send
from models.common.pages import dated_sections, link_list
from models.common.runner import cli
from models.common.sources import Source, custom, hf, html

SITEMAP = "https://api-docs.deepseek.com/sitemap.xml"

NEWS_URL = re.compile(r"<loc>(https://api-docs\.deepseek\.com/news/news(\d{6})/?)</loc>")

def news_date(url: str) -> str | None:
	"""Read the release date from a /news/newsYYMMDD/ URL.

	Args:
		url (str): News page URL.

	Returns:
		str | None: Date as ``YYYY-MM-DD``, or None.
	"""

	match = re.search(r"news(\d{2})(\d{2})(\d{2})", url)

	return f"20{match.group(1)}-{match.group(2)}-{match.group(3)}" if match else None

def latest_news(client: primp.Client, source: Source) -> str:
	"""Return the HTML of the newest DeepSeek news page, found through the sitemap.

	Args:
		client (primp.Client): Client from ``new_client``.
		source (Source): Source whose URL is the docs sitemap.

	Returns:
		str: HTML of the newest news page, whose sidebar lists every release.
	"""

	sitemap = send(client, source.url).text
	pages = NEWS_URL.findall(sitemap)

	if not pages:
		raise FetchError("no /news/ pages in the sitemap")

	newest = max(pages, key=lambda page: page[1])[0]

	return fetch_html(client, Source("html", newest))

LABEL = "DeepSeek"

SOURCES = [
	custom("html", SITEMAP, latest_news, link_list(r"^/news/news\d{6}/?$", news_date, scope="nav.menu")),
	hf("deepseek-ai"),
	html("https://api-docs.deepseek.com/updates", dated_sections()),
]

if __name__ == "__main__":
	cli(__file__, LABEL, SOURCES)
