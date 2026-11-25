"""Sources for AI21 Labs (Jamba) model releases. The blog runs on WordPress, so its REST API returns the posts as JSON."""

from models.common.runner import cli
from models.common.sources import api, hf

SOURCES = [
	api("https://www.ai21.com/wp-json/wp/v2/posts?per_page=10&_fields=date,title,link"),
	hf("ai21labs"),
]

if __name__ == "__main__":
	cli(__file__, SOURCES)
