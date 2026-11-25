"""Sources for Anthropic (Claude) model releases.

Anthropic has no feed; the news page and the API release notes are converted to markdown.
"""

from models.common.runner import cli
from models.common.sources import html

SOURCES = [
	html("https://www.anthropic.com/news"),
	html("https://platform.claude.com/docs/en/release-notes/overview"),
]

if __name__ == "__main__":
	cli(__file__, SOURCES)
