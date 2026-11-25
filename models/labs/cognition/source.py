"""Sources for Cognition (SWE models, Devin, Windsurf) model releases."""

from models.common.runner import cli
from models.common.sources import html, rss

SOURCES = [
	html("https://cognition.com/blog"),
	rss("https://docs.devin.ai/release-notes/overview/rss.xml"),
]

if __name__ == "__main__":
	cli(__file__, SOURCES)
