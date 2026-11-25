"""Sources for Deep Cogito model releases. Hugging Face is the main signal; the research page has no dates."""

from models.common.pages import link_list
from models.common.runner import cli
from models.common.sources import hf, html

SOURCES = [
	hf("deepcogito"),
	html("https://www.deepcogito.com/research", link_list(r"^/research/[^/]+$")),
]

if __name__ == "__main__":
	cli(__file__, SOURCES)
