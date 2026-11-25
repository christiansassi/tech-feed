"""Sources for Anthropic (Claude) model releases.

Anthropic has no feed: the news page is read as a list of article cards, and the API release notes as a changelog with one dated heading per entry.
"""

from models.common.pages import dated_sections, link_list
from models.common.runner import cli
from models.common.sources import html

LABEL = "Anthropic"

SOURCES = [
	html("https://www.anthropic.com/news", link_list(r"^/(?:news/(?!(?:announcements|product|policy|science|economics|features|research|societal-impacts|interpretability|alignment|company|events)$)[a-z0-9-]+|claude-[a-z0-9-]+)$")),
	html("https://platform.claude.com/docs/en/release-notes/overview", dated_sections()),
]

if __name__ == "__main__":
	cli(__file__, LABEL, SOURCES)
