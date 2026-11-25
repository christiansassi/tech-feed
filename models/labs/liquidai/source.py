"""Sources for Liquid AI (LFM) model releases."""

from models.common.pages import link_list
from models.common.runner import cli
from models.common.sources import hf, html

SOURCES = [
	html("https://www.liquid.ai/news/models", link_list(r"^/(?:news|blog)/[^/]+$")),
	hf("LiquidAI"),
]

if __name__ == "__main__":
	cli(__file__, SOURCES)
