"""Sources for Liquid AI (LFM) model releases."""

from models.common.runner import cli
from models.common.sources import hf, html

SOURCES = [
	html("https://www.liquid.ai/news/models"),
	hf("LiquidAI"),
]

if __name__ == "__main__":
	cli(__file__, SOURCES)
