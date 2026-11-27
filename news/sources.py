"""List of the news sources read every hour.

Most sources are RSS or Atom feeds. The blogs of the followed model labs reuse
the source already defined in ``models/labs/<lab>/source.py``, so each page is
described once. ``label`` is the name shown on the site, so sources of the same
publisher share it.
"""

import importlib
import json
import re
from dataclasses import dataclass

from models.common.items import extract_feed, item, newest_first, text_of
from models.common.pages import link_list
from models.common.sources import Source, api, html, rss
from models.common.validation import require_text, require_type

MSRC_API = "https://www.microsoft.com/msstoreapiprod/api/msrc/Search?pageType=blog&top=20&skip=0"

MSRC_BASE = "https://www.microsoft.com/en-us/msrc"

APPLE_BLOG = "https://security.apple.com/blog/"

NEXT_DATA = re.compile(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.DOTALL)

# Japanese letters and CJK ideographs: the MSRC blog mixes in the posts of its Japanese team.
JAPANESE = re.compile(r"[぀-ヿ一-鿿]")

@dataclass(frozen=True)
class NewsSource:
	"""One news source.

	Attributes:
		slug (str): Identifier in the raw files, lowercase with hyphens.
		label (str): Publisher name shown on the site.
		source (Source): How to fetch the source and extract its items.
	"""

	slug: str
	label: str
	source: Source

def feed(slug: str, label: str, url: str) -> NewsSource:
	"""Return a news source read from an RSS or Atom feed.

	Args:
		slug (str): Identifier in the raw files.
		label (str): Publisher name shown on the site.
		url (str): Absolute URL of the feed.

	Returns:
		NewsSource: Source of kind ``"rss"``.
	"""

	require_text("slug", slug)
	require_text("label", label)

	return NewsSource(slug, label, rss(url))

def lab(slug: str, name: str, url_prefix: str) -> NewsSource:
	"""Return the news source of a model lab, reusing the source defined for the Models section.

	Args:
		slug (str): Identifier in the raw files.
		name (str): Folder of the lab in ``models/labs``.
		url_prefix (str): Start of the URL of the lab source to reuse.

	Returns:
		NewsSource: The lab source, labeled with the lab name.
	"""

	require_text("slug", slug)
	require_text("name", name)
	require_text("url_prefix", url_prefix)

	module = importlib.import_module(f"models.labs.{name}.source")
	source = next((source for source in module.SOURCES if source.url.startswith(url_prefix)), None)

	if source is None:
		raise ValueError(f"no source of {name} starts with {url_prefix}")

	return NewsSource(slug, module.LABEL, source)

def extract_discussion(content: dict, source_url: str) -> list[dict]:
	"""Read a link aggregator feed so that each item links to its page on the aggregator, not to the article it points to.

	The card of such an item names the aggregator as its source, so its link
	goes to the aggregator too; the page there links to the article.

	Args:
		content (dict): Feed converted by xmltodict, whose items have a ``comments`` element.
		source_url (str): Feed URL.

	Returns:
		list[dict]: Items with the aggregator page as ``url`` and the article link as ``target``, newest first.
	"""

	require_type("content", content, dict)

	channel = dict(content.get("rss", {}).get("channel", {}))
	entries = channel.get("item", [])
	entries = [entries] if isinstance(entries, dict) else entries
	targets = {text_of(entry.get("comments")): text_of(entry.get("link")) for entry in entries if text_of(entry.get("comments"))}
	channel["item"] = [dict(entry, link=text_of(entry.get("comments")) or entry.get("link")) for entry in entries]

	# The article link stays as ``target``, so the filters can tell what the item is about. The feed summary only lists the links and the points, so it is not an intro.
	return [dict(entry, target=targets.get(entry["url"]), summary=None) for entry in extract_feed({"rss": {"channel": channel}}, source_url)]

def extract_msrc(content: dict, source_url: str) -> list[dict]:
	"""Turn the MSRC blog search API response into items, leaving out the posts in Japanese.

	Args:
		content (dict): JSON response with a ``results`` list.
		source_url (str): API URL.

	Returns:
		list[dict]: One item per English post, newest first.
	"""

	require_type("content", content, dict)

	posts = [post for post in content.get("results", []) if not JAPANESE.search(post.get("title") or "")]

	return newest_first([item(post.get("title"), post.get("publishedDate"), MSRC_BASE + post["permalink"] if post.get("permalink") else None, post.get("blurb")) for post in posts])

def extract_apple(page_html: str, source_url: str) -> list[dict]:
	"""Read the posts of the Apple Security Research blog from the page data, since its links are added by script.

	Args:
		page_html (str): Page HTML with a ``__NEXT_DATA__`` script.
		source_url (str): Page URL.

	Returns:
		list[dict]: One item per post, newest first.
	"""

	require_type("page_html", page_html, str)

	match = NEXT_DATA.search(page_html)

	if match is None:
		raise ValueError("no __NEXT_DATA__ script in the page")

	posts = json.loads(match.group(1))["props"]["pageProps"].get("blogs", [])

	return newest_first([item(post.get("title"), post.get("date"), f"{APPLE_BLOG}{post['slug']}/" if post.get("slug") else None, post.get("description")) for post in posts])

SOURCES = [
	feed("abuse-ch", "abuse.ch", "https://abuse.ch/rss/"),
	feed("ahead-of-ai", "Ahead of AI", "https://magazine.sebastianraschka.com/feed"),
	feed("ahnlab-asec", "AhnLab ASEC", "https://asec.ahnlab.com/en/feed/"),
	feed("amnesty-security-lab", "Amnesty Security Lab", "https://securitylab.amnesty.org/feed/"),
	feed("anquanke", "Anquanke", "https://api.anquanke.com/data/v1/rss"),
	lab("anthropic", "anthropic", "https://www.anthropic.com/news"),
	NewsSource("anthropic-research", "Anthropic", html("https://www.anthropic.com/research", link_list(r"^/research/(?!team/)[a-z0-9-]+$"))),
	feed("apple-machine-learning", "Apple Machine Learning Research", "https://machinelearning.apple.com/rss.xml"),
	NewsSource("apple-security-research", "Apple Security Research", html(APPLE_BLOG, extract_apple)),
	feed("bair", "BAIR", "https://bair.berkeley.edu/blog/feed.xml"),
	feed("binarly", "Binarly", "https://www.binarly.io/blog/rss.xml"),
	feed("check-point-research", "Check Point Research", "https://research.checkpoint.com/feed/"),
	feed("circl", "CIRCL", "https://www.circl.lu/pub/rss.xml"),
	feed("cisco-talos", "Cisco Talos", "https://blog.talosintelligence.com/rss/"),
	feed("citizen-lab", "Citizen Lab", "https://citizenlab.ca/feed/"),
	feed("cloudflare-security", "Cloudflare", "https://blog.cloudflare.com/tag/security/rss/"),
	feed("crowdstrike", "CrowdStrike", "https://www.crowdstrike.com/en-us/blog/feed/"),
	feed("csa-singapore", "CSA Singapore", "https://www.csa.gov.sg/alerts-and-advisories/rss.xml"),
	feed("datadog-security-labs", "Datadog Security Labs", "https://securitylabs.datadoghq.com/rss/feed.xml"),
	lab("deepseek", "deepseek", "https://api-docs.deepseek.com/sitemap.xml"),
	feed("didier-stevens", "Didier Stevens", "https://blog.didierstevens.com/feed/"),
	feed("doublepulsar", "DoublePulsar", "https://doublepulsar.com/feed"),
	feed("doyensec", "Doyensec", "https://blog.doyensec.com/atom.xml"),
	feed("elastic-security-labs", "Elastic Security Labs", "https://www.elastic.co/security-labs/rss/feed.xml"),
	feed("embrace-the-red", "Embrace The Red", "https://embracethered.com/blog/index.xml"),
	feed("github-security", "GitHub", "https://github.blog/security/feed/"),
	feed("google-ai", "Google", "https://blog.google/technology/ai/rss/"),
	feed("google-deepmind", "Google DeepMind", "https://deepmind.google/blog/rss.xml"),
	feed("google-online-security", "Google Online Security Blog", "https://security.googleblog.com/feeds/posts/default"),
	feed("google-project-zero", "Google Project Zero", "https://projectzero.google/feed.xml"),
	feed("google-research", "Google Research", "https://research.google/blog/rss/"),
	feed("google-threat-intelligence", "Google Threat Intelligence", "https://feeds.feedburner.com/threatintelligence/pvexyqv7v0v"),
	feed("greynoise", "GreyNoise", "https://www.greynoise.io/blog/rss.xml"),
	feed("group-ib", "Group-IB", "https://www.group-ib.com/blog/feed/"),
	NewsSource("hacker-news", "Hacker News", Source("rss", "https://hnrss.org/frontpage?points=300", extract=extract_discussion)),
	feed("hexacorn", "Hexacorn", "https://www.hexacorn.com/blog/feed/"),
	feed("hugging-face", "Hugging Face", "https://huggingface.co/blog/feed.xml"),
	feed("import-ai", "Import AI", "https://importai.substack.com/feed"),
	feed("interconnects", "Interconnects", "https://www.interconnects.ai/feed"),
	feed("jpcert", "JPCERT/CC", "https://blogs.jpcert.or.jp/en/atom.xml"),
	feed("krebs-on-security", "Krebs on Security", "https://krebsonsecurity.com/feed/"),
	feed("lets-encrypt", "Let's Encrypt", "https://letsencrypt.org/feed.xml"),
	lab("meta", "meta", "https://ai.meta.com/blog/"),
	feed("metr", "METR", "https://metr.org/feed.xml"),
	NewsSource("microsoft-msrc", "Microsoft MSRC", api(MSRC_API, extract_msrc)),
	feed("microsoft-research", "Microsoft Research", "https://www.microsoft.com/en-us/research/feed/"),
	feed("microsoft-security", "Microsoft Security", "https://www.microsoft.com/en-us/security/blog/feed/"),
	lab("minimax-blog", "minimax", "https://www.minimax.io/blog"),
	lab("minimax-news", "minimax", "https://www.minimax.io/api/news"),
	lab("mistral", "mistral", "https://mistral.ai/news/rss"),
	lab("moonshot", "moonshotai", "https://www.kimi.ai/blog/"),
	feed("mozilla-security", "Mozilla", "https://blog.mozilla.org/security/feed/"),
	NewsSource("ncc-group", "NCC Group", html("https://www.nccgroup.com/research/research-articles/", link_list(r"^/research/[a-z0-9-]+/?$", scope=".c-research__title, .c-research", title=".c-research__title"))),
	feed("objective-see", "Objective-See", "https://objective-see.org/rss.xml"),
	feed("openai", "OpenAI", "https://openai.com/news/rss.xml"),
	feed("ostif", "OSTIF", "https://ostif.org/feed/"),
	feed("owasp-genai", "OWASP GenAI Security Project", "https://genai.owasp.org/feed/"),
	feed("portswigger-research", "PortSwigger Research", "https://portswigger.net/research/rss"),
	feed("projectdiscovery", "ProjectDiscovery", "https://projectdiscovery.io/rss.xml"),
	feed("qianxin-xlab", "QiAnXin XLab", "https://blog.xlab.qianxin.com/rss/"),
	feed("quarkslab", "Quarkslab", "https://blog.quarkslab.com/feeds/all.rss.xml"),
	lab("qwen", "qwen", "https://qwen.ai/api/v2/article/retrieval"),
	feed("rapid7", "Rapid7", "https://www.rapid7.com/rss.xml"),
	feed("recorded-future", "Recorded Future", "https://www.recordedfuture.com/feed"),
	feed("red-canary", "Red Canary", "https://redcanary.com/blog/feed/"),
	feed("reversinglabs", "ReversingLabs", "https://www.reversinglabs.com/blog/rss.xml"),
	feed("sans-isc", "SANS Internet Storm Center", "https://isc.sans.edu/rssfeed_full.xml"),
	feed("schneier-on-security", "Schneier on Security", "https://www.schneier.com/feed/atom/"),
	feed("securelist", "Securelist", "https://securelist.com/feed/"),
	feed("securityweek", "SecurityWeek", "https://www.securityweek.com/feed/"),
	feed("sekoia", "Sekoia", "https://blog.sekoia.io/feed/"),
	feed("sentinellabs", "SentinelLabs", "https://www.sentinelone.com/labs/feed/"),
	NewsSource("shadowserver", "Shadowserver", html("https://www.shadowserver.org/news-insights/", link_list(r"^/news/[a-z0-9-]+/?$"))),
	feed("specterops", "SpecterOps", "https://specterops.io/feed/"),
	feed("symantec", "Symantec", "https://www.security.com/rss/v1/blogs/rss.xml/221"),
	feed("synacktiv", "Synacktiv", "https://www.synacktiv.com/feed/lastblog.xml"),
	feed("team-cymru", "Team Cymru", "https://www.team-cymru.com/post/rss.xml"),
	lab("tencent-hunyuan", "tencent", "https://api.hunyuan.tencent.com/api/blog/publicList"),
	feed("tencent-xuanwu", "Tencent Xuanwu Lab", "https://xlab.tencent.com/en/atom.xml"),
	feed("the-dfir-report", "The DFIR Report", "https://thedfirreport.com/feed/"),
	feed("the-hacker-news", "The Hacker News", "https://feeds.feedburner.com/TheHackersNews"),
	lab("thinkingmachines-blog", "thinkingmachines", "https://thinkingmachines.ai/blog/"),
	lab("thinkingmachines-news", "thinkingmachines", "https://thinkingmachines.ai/news/"),
	feed("tldr-sec", "tl;dr sec", "https://rss.beehiiv.com/feeds/xgTKUmMmUm.xml"),
	feed("trail-of-bits", "Trail of Bits", "https://blog.trailofbits.com/feed/"),
	feed("trend-micro", "Trend Micro", "https://www.trendaisecurity.com/en-us/resources-insights/research/rss.xml"),
	feed("unit-42", "Unit 42", "https://unit42.paloaltonetworks.com/feed/"),
	feed("volexity", "Volexity", "https://www.volexity.com/feed/"),
	feed("watchtowr", "watchTowr Labs", "https://labs.watchtowr.com/rss/"),
	feed("welivesecurity", "WeLiveSecurity", "https://www.welivesecurity.com/en/rss/feed/"),
	feed("wiz-research", "Wiz", "https://www.wiz.io/feed/rss.xml"),
	lab("xai", "xai", "https://x.ai/news"),
	lab("xiaomi", "xiaomi", "https://mimo.xiaomi.com/"),
	feed("xpn", "XPN InfoSec Blog", "https://blog.xpnsec.com/rss.xml"),
	lab("zai", "zai", "https://www.zhipuai.cn/api/articles"),
	feed("zellic", "Zellic", "https://www.zellic.io/blog/rss.xml"),
	feed("zero-day-initiative", "Zero Day Initiative", "https://www.thezdi.com/blog?format=rss"),
	feed("zscaler-threatlabz", "Zscaler ThreatLabz", "https://www.zscaler.com/blogs/feeds/security-research"),
]
