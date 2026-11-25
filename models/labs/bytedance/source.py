"""Sources for ByteDance Seed model releases. The blog is rendered with JavaScript; its article list comes from this API (article_type=2 is the blog). Some posts only have Chinese fields."""

from models.common.runner import cli
from models.common.sources import api, hf

SOURCES = [
	api("https://seed.bytedance.com/api/get_article_list_v2?article_type=2&count=10&order_desc=true"),
	hf("ByteDance-Seed"),
]

if __name__ == "__main__":
	cli(__file__, SOURCES)
