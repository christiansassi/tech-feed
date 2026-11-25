"""Sources for Reka AI model releases."""

from models.common.runner import cli
from models.common.sources import hf, html

SOURCES = [
	html("https://reka.ai/news"),
	hf("RekaAI"),
]

if __name__ == "__main__":
	cli(__file__, SOURCES)
