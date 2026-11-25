"""Sources for Google model releases: Gemini, Gemma, Veo, Imagen, Nano Banana, Lyria, Genie, Robotics and research models.

The DeepMind feed covers almost every family; the Gemini API changelog adds model ids and releases the blog skips; the Gemma page lists Gemma variants; Hugging Face adds open research models; the Google Research feed adds research models.
"""

from models.common.runner import cli
from models.common.sources import hf, html, rss

SOURCES = [
	rss("https://deepmind.google/blog/rss.xml"),
	html("https://ai.google.dev/gemini-api/docs/changelog"),
	html("https://ai.google.dev/gemma/docs/releases"),
	hf("google"),
	rss("https://research.google/blog/rss/"),
]

if __name__ == "__main__":
	cli(__file__, SOURCES)
