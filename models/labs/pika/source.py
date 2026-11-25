"""Sources for Pika video model releases."""

from models.common.runner import cli
from models.common.sources import rss

SOURCES = [
	rss("https://pika.art/blog/feed.xml"),
]

if __name__ == "__main__":
	cli(__file__, SOURCES)
