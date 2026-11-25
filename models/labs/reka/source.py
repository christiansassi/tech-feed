"""Sources for Reka AI model releases."""

from models.common.pages import link_list
from models.common.runner import cli
from models.common.sources import hf, html

LABEL = "Reka AI"

SOURCES = [
	html("https://reka.ai/news", link_list(r"^/news/[^/]+$")),
	hf("RekaAI"),
]

if __name__ == "__main__":
	cli(__file__, LABEL, SOURCES)
