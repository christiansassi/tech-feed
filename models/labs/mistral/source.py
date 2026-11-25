"""Sources for Mistral AI model releases."""

from models.common.runner import cli
from models.common.sources import hf, rss

LABEL = "Mistral AI"

SOURCES = [
	rss("https://mistral.ai/news/rss"),
	hf("mistralai"),
]

if __name__ == "__main__":
	cli(__file__, LABEL, SOURCES)
