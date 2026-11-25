"""Sources for MiniMax and Hailuo model releases. Hailuo launches appear in the news section, whose list comes from the news API."""

from models.common.runner import cli
from models.common.sources import api, hf, html

SOURCES = [
	html("https://www.minimax.io/blog"),
	hf("MiniMaxAI"),
	api("https://www.minimax.io/api/news?page=1&locale=en"),
]

if __name__ == "__main__":
	cli(__file__, SOURCES)
