"""Sources for OpenAI model releases: the news feed and the API changelog, which lists model ids."""

from models.common.runner import cli
from models.common.sources import hf, html, rss

SOURCES = [
	rss("https://openai.com/news/rss.xml"),
	html("https://developers.openai.com/api/docs/changelog"),
	hf("openai"),
]

if __name__ == "__main__":
	cli(__file__, SOURCES)
