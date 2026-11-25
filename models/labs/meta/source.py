"""Sources for Meta AI model releases.

The newsroom AI feed is the most current source. ai.meta.com rejects requests
without browser navigation headers, so they are sent with the blog request.
"""

from models.common.pages import link_list
from models.common.runner import cli
from models.common.sources import hf, html, rss

NAVIGATION_HEADERS = {"Accept": "text/html,application/xhtml+xml", "Sec-Fetch-Dest": "document", "Sec-Fetch-Mode": "navigate", "Sec-Fetch-Site": "none"}

SOURCES = [
	rss("https://about.fb.com/news/tag/ai/feed/"),
	hf("facebook"),
	html("https://ai.meta.com/blog/", link_list(r"^/blog/[^/]+/?$"), headers=NAVIGATION_HEADERS),
]

if __name__ == "__main__":
	cli(__file__, SOURCES)
