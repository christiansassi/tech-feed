"""Sources for IBM Granite model releases. Hugging Face is the most reliable signal; the IBM feeds cover all IBM news."""

from models.common.runner import cli
from models.common.sources import hf, rss

SOURCES = [
	hf("ibm-granite"),
	rss("https://newsroom.ibm.com/announcements?pagetemplate=rss"),
	rss("https://research.ibm.com/rss"),
]

if __name__ == "__main__":
	cli(__file__, SOURCES)
