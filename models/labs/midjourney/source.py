"""Sources for Midjourney model releases.

The updates site is private and midjourney.com is behind a bot challenge, so the help center API is used: the Version article lists every model version, and the newest articles show new features. Both lag behind launches.
"""

from models.common.runner import cli
from models.common.sources import api

SOURCES = [
	api("https://docs.midjourney.com/api/v2/help_center/en-us/articles/32199405667853.json"),
	api("https://docs.midjourney.com/api/v2/help_center/en-us/articles.json?sort_by=created_at&sort_order=desc&per_page=30"),
]

if __name__ == "__main__":
	cli(__file__, SOURCES)
