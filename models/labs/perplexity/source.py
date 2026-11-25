"""Sources for Perplexity (Sonar, PPLX) model releases. The blog is behind a bot challenge, so the API docs changelog is used; its item dates change on every docs rebuild."""

from models.common.runner import cli
from models.common.sources import hf, rss

SOURCES = [
	rss("https://docs.perplexity.ai/docs/resources/changelog/rss.xml"),
	hf("perplexity-ai"),
]

if __name__ == "__main__":
	cli(__file__, SOURCES)
