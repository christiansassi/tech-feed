"""Sources for StepFun model releases.

Hugging Face is the main signal. The news site (Chinese only) is a JavaScript
app with no data API: its article list is compiled into the main bundle
``/assets/index-<hash>.js``. The bundle name changes on every deploy, so it is
read from the news page first, then each article's slug, date, title and tags
are extracted from the bundle, with the first paragraph of each article as summary.
"""

import re

import primp

from models.common.http import FetchError, send
from models.common.items import item, newest_first
from models.common.runner import cli
from models.common.sources import Source, custom, hf
from models.common.validation import require_type

NEWS_PAGE = "https://www.stepfun.com/news"

BUNDLE = re.compile(r"/assets/index-[\w-]+\.js")

ARTICLE = re.compile(r'\{slug:"([^"]+)",date:"(\d{4}-\d{2}-\d{2})",dateLabel:"[^"]*",title:"([^"]*)"(?:,thumb:"[^"]*")?,tags:\[([^\]]*)\](?:,blocks:\[\{t:"p",md:"((?:[^"\\]|\\.)*)")?')

def bundle_articles(client: primp.Client, source: Source) -> list[dict]:
	"""Return the news articles compiled into the StepFun site bundle.

	Args:
		client (primp.Client): Client from ``new_client``.
		source (Source): Source whose URL is the news page.

	Returns:
		list[dict]: Articles with ``slug``, ``url``, ``date``, ``title``, ``tags`` and ``summary``.
	"""

	page = send(client, source.url).text
	bundle = BUNDLE.search(page)

	if not bundle:
		raise FetchError("main bundle not found in the news page")

	script = send(client, "https://www.stepfun.com" + bundle.group(0)).text
	articles = []

	for slug, date, title, tags, first_paragraph in ARTICLE.findall(script):
		articles.append({
			"slug": slug,
			"url": f"{NEWS_PAGE}/{slug}",
			"date": date,
			"title": title,
			"tags": re.findall(r'"([^"]*)"', tags),
			"summary": first_paragraph.replace("**", "") or None,
		})

	if not articles:
		raise FetchError("no articles found in the bundle")

	return articles

def extract_articles(articles: list[dict], source_url: str) -> list[dict]:
	"""Map the articles read from the bundle to items.

	Args:
		articles (list[dict]): Articles from ``bundle_articles``.
		source_url (str): News page URL (unused).

	Returns:
		list[dict]: One item per article, newest first.
	"""

	require_type("articles", articles, list)

	return newest_first([item(a["title"], a["date"], a["url"], a["summary"]) for a in articles])

SOURCES = [
	hf("stepfun-ai"),
	custom("api", NEWS_PAGE, bundle_articles, extract_articles),
]

if __name__ == "__main__":
	cli(__file__, SOURCES)
