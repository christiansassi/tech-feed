"""Sources for StepFun model releases.

Hugging Face is the main signal. The news site (Chinese only) is a JavaScript
app with no data API: its article list is compiled into the main bundle
``/assets/index-<hash>.js``. The bundle name changes on every deploy, so it is
read from the news page first, then each article's slug, date, title and tags
are extracted from the bundle.
"""

import re

import primp

from models.common.http import FetchError, send
from models.common.runner import cli
from models.common.sources import Source, custom, hf

NEWS_PAGE = "https://www.stepfun.com/news"

BUNDLE = re.compile(r"/assets/index-[\w-]+\.js")

ARTICLE = re.compile(r'\{slug:"([^"]+)",date:"(\d{4}-\d{2}-\d{2})",dateLabel:"[^"]*",title:"([^"]*)"(?:,thumb:"[^"]*")?,tags:\[([^\]]*)\]')


def bundle_articles(client: primp.Client, source: Source) -> list[dict]:
	"""Return the news articles compiled into the StepFun site bundle.

	Args:
		client (primp.Client): Client from ``new_client``.
		source (Source): Source whose URL is the news page.

	Returns:
		list[dict]: Articles with ``slug``, ``url``, ``date``, ``title`` and ``tags``, newest first.
	"""

	page = send(client, source.url).text
	bundle = BUNDLE.search(page)

	if not bundle:
		raise FetchError("main bundle not found in the news page")

	script = send(client, "https://www.stepfun.com" + bundle.group(0)).text
	articles = []

	for slug, date, title, tags in ARTICLE.findall(script):
		articles.append({
			"slug": slug,
			"url": f"{NEWS_PAGE}/{slug}",
			"date": date,
			"title": title,
			"tags": re.findall(r'"([^"]*)"', tags),
		})

	if not articles:
		raise FetchError("no articles found in the bundle")

	return sorted(articles, key=lambda article: article["date"], reverse=True)


SOURCES = [
	hf("stepfun-ai"),
	custom("api", NEWS_PAGE, bundle_articles),
]

if __name__ == "__main__":
	cli(__file__, SOURCES)
