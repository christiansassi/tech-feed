"""Sources for Meta AI model releases. The newsroom AI feed is the most current source; ai.meta.com rejects requests without browser navigation headers."""

from models.common.runner import cli
from models.common.sources import hf, html, rss

SOURCES = [
	rss("https://about.fb.com/news/tag/ai/feed/"),
	hf("facebook"),
	html("https://ai.meta.com/blog/", headers={"Accept": "text/html,application/xhtml+xml", "Sec-Fetch-Dest": "document", "Sec-Fetch-Mode": "navigate", "Sec-Fetch-Site": "none"}),
]

if __name__ == "__main__":
	cli(__file__, SOURCES)
