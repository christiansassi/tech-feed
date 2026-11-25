"""Sources for Stability AI model releases."""

from models.common.runner import cli
from models.common.sources import hf, rss

SOURCES = [
	rss("https://stability.ai/news-updates?format=rss"),
	hf("stabilityai"),
]

if __name__ == "__main__":
	cli(__file__, SOURCES)
