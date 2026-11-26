"""Sources for Thinking Machines model releases. Hugging Face lists the open weights; the news page announces each Inkling model with its date, and the blog holds the research posts."""

from models.common.pages import link_list
from models.common.runner import cli
from models.common.sources import hf, html

LABEL = "Thinking Machines"

SOURCES = [
	hf("thinkingmachines"),
	html("https://thinkingmachines.ai/news/", link_list(r"^/news/[^/]+/$", title=".post-title")),
	html("https://thinkingmachines.ai/blog/", link_list(r"^/blog/[^/]+/$", title=".post-title")),
]

if __name__ == "__main__":
	cli(__file__, LABEL, SOURCES)
