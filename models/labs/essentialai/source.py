"""Sources for Essential AI (Rnj) model releases. The website is stale, so Hugging Face is the main signal."""

from models.common.runner import cli
from models.common.sources import hf, html

SOURCES = [
	hf("EssentialAI"),
	html("https://www.essential.ai/research"),
]

if __name__ == "__main__":
	cli(__file__, SOURCES)
