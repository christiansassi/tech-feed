"""Sources for Google model releases: Gemini, Gemma, Veo, Imagen, Nano Banana, Lyria, Genie, Robotics and research models.

The DeepMind feed covers almost every family; the Gemini API changelog (read as
markdown, one item per change) adds model ids and releases the blog skips; the
Gemma page lists Gemma variants; Hugging Face adds open research models; the
Google Research feed adds research models.
"""

from models.common.pages import dated_sections, markdown_entries
from models.common.runner import cli
from models.common.sources import hf, html, rss

GEMINI_CHANGELOG = "https://aistudio.google.com/docs/changelog"

LABEL = "Google"

SOURCES = [
	rss("https://deepmind.google/blog/rss.xml"),
	html(f"{GEMINI_CHANGELOG}.md", markdown_entries(GEMINI_CHANGELOG)),
	html("https://ai.google.dev/gemma/docs/releases", dated_sections("h2")),
	hf("google"),
	rss("https://research.google/blog/rss/"),
]

if __name__ == "__main__":
	cli(__file__, LABEL, SOURCES)
