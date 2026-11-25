"""Sources for Luma AI video model releases. The API changelog is stale (last entry about two years old) and is not used."""

from models.common.pages import link_list
from models.common.runner import cli
from models.common.sources import html

SOURCES = [
	html("https://lumalabs.ai/news", link_list(r"^/news/[^/]+$")),
]

if __name__ == "__main__":
	cli(__file__, SOURCES)
