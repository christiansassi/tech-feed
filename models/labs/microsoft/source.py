"""Sources for Microsoft AI (MAI) model releases. Posts use custom WordPress post types, so the plain /feed/ is empty."""

from models.common.runner import cli
from models.common.sources import hf, rss

LABEL = "Microsoft"

SOURCES = [
	rss("https://microsoft.ai/feed/?post_type=new"),
	rss("https://microsoft.ai/feed/?post_type=model"),
	hf("microsoft", search="MAI"),
]

if __name__ == "__main__":
	cli(__file__, LABEL, SOURCES)
