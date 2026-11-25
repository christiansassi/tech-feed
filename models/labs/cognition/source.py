"""Sources for Cognition (SWE models, Devin, Windsurf) model releases."""

from models.common.pages import link_list
from models.common.runner import cli
from models.common.sources import html, rss

LABEL = "Cognition"

SOURCES = [
	html("https://cognition.com/blog", link_list(r"^/blog/[^/]+$")),
	rss("https://docs.devin.ai/release-notes/overview/rss.xml"),
]

if __name__ == "__main__":
	cli(__file__, LABEL, SOURCES)
