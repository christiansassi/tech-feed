"""Sources for Moonshot AI (Kimi) model releases."""

from models.common.pages import link_list
from models.common.runner import cli
from models.common.sources import hf, html

SOURCES = [
	html("https://www.kimi.ai/blog/", link_list(r"^/blog/[^/]+/?$")),
	hf("moonshotai"),
]

if __name__ == "__main__":
	cli(__file__, SOURCES)
