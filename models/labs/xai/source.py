"""Sources for xAI (Grok) model releases."""

from models.common.runner import cli
from models.common.sources import html

SOURCES = [
	html("https://x.ai/news"),
	html("https://docs.x.ai/docs/release-notes"),
]

if __name__ == "__main__":
	cli(__file__, SOURCES)
