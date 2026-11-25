"""Sources for Poolside (Laguna) model releases. The blog is a SvelteKit app; __data.json holds its post list."""

from models.common.runner import cli
from models.common.sources import api, hf

SOURCES = [
	api("https://poolside.ai/blog/__data.json"),
	hf("poolside"),
]

if __name__ == "__main__":
	cli(__file__, SOURCES)
