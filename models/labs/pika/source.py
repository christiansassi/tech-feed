"""Sources for Pika video model releases."""

from models.common.runner import cli
from models.common.sources import rss

LABEL = "Pika"

SOURCES = [
	rss("https://pika.art/blog/feed.xml"),
]

if __name__ == "__main__":
	cli(__file__, LABEL, SOURCES)
