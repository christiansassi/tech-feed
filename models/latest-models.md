## Parameters

```
BASE_URL = https://christiansassi.github.io/tech-feed/models/
LEVEL    = medium    # light | medium | full
LABS     = all       # all, or a comma-separated list of lab slugs such as: qwen, openai, xiaomi
SINCE    = latest    # latest, or a Unix timestamp in seconds: report every release from that time on
```

## Task

Find the most recent models released by each AI lab listed on BASE_URL and report them. Use only the JSON files described below. Do not open the article links inside them and do not search the web.

## Steps

1. Fetch `{BASE_URL}index.json`. Its `labs` array has one entry per lab with:
	- `slug`: lab identifier, such as `openai`
	- `label`: lab name for display, such as `OpenAI`
	- `urls`: the paths of the three files of the lab, relative to BASE_URL, keyed by level (`light`, `medium`, `full`)
2. For every lab in `labs` (or only the labs whose `slug` is in LABS), fetch `{BASE_URL}{urls[LEVEL]}`. Fetch one lab at a time or in parallel; every lab is independent.
3. Each lab file has this shape:
	```
	{
		"slug": "qwen",
		"label": "Qwen",
		"level": "medium",
		"generated_at": 1795613766,
		"sources": [
			{
				"rank": 1,
				"type": "api",
				"url": "...",
				"fetched_at": 1795613760,
				"status": "ok",
				"error": null,
				"items_dropped": 0,
				"items": [
					{"title": "...", "date": 1794787200, "url": "...", "summary": "..."}
				]
			}
		]
	}
	```
	- `sources` are ordered from the main source (`rank` 1) to the least important. `type` is `api`, `rss` or `html` for the lab's own site and `hf` for its Hugging Face organization.
	- Skip a source whose `status` is not `ok`.
	- `date` is a Unix timestamp in seconds (UTC). When the source gives only the day, it is midnight UTC of that day. It can be `null`.
	- `summary` exists from level `medium` and `body` from level `full`; both can be `null`.
4. In each lab file, keep only the items that announce a new model or a new version of a model made by that lab (language, vision, image, video, audio, speech, embedding, code or any other model). Use the title and, when present, the summary to decide. Discard:
	- research papers, benchmarks and technical reports that do not release a model
	- product features, apps, pricing, API changes, partnerships, events, hiring and company news
	- models of other labs that this lab only makes available, for example in its app or API
	- a model that becomes generally available or reaches a new region after it was already announced
	- on Hugging Face (`type` `hf`): datasets, Spaces, tokenizers, quantized or converted copies (GGUF, AWQ, GPTQ, FP8, NVFP4, INT4, MLX, ONNX), adapters and LoRAs, and fine-tunes of models made by other labs
5. Several items can describe the same release: a blog post, a changelog entry and the Hugging Face repositories of its sizes or variants. Treat them as one model, named as the lab names the release (for example `Qwen4-Max`, not `Qwen/Qwen4-Max-Instruct-2611-FP8`). Its date and link come from one item: the lab's own announcement when there is one, otherwise the item with the earliest date.
6. Choose the models to report. A `since` field in a lab's entry of `index.json`, when present, replaces SINCE for that lab.
	- When SINCE is `latest`: find the kept model with the highest `date`, and report it together with every other kept model whose `date` falls on the same UTC day, newest first. Use models with `date` `null` only when the lab has no dated model, and then report their `date` as `null`.
	- When SINCE is a timestamp: report every kept model whose `date` is on or after it, newest first, and skip models whose `date` is `null`.
7. If a lab file cannot be fetched, or no item in it is a model release, report the lab with an empty `models` list.

## Output

Reply with one JSON object and nothing else: no prose, no code fence. It must validate against this JSON Schema:

```
{
	"$schema": "https://json-schema.org/draft/2020-12/schema",
	"type": "object",
	"required": ["labs"],
	"additionalProperties": false,
	"properties": {
		"labs": {
			"type": "array",
			"items": {
				"type": "object",
				"required": ["slug", "label", "models"],
				"additionalProperties": false,
				"properties": {
					"slug": {"type": "string", "pattern": "^[a-z0-9]+(-[a-z0-9]+)*$"},
					"label": {"type": "string"},
					"models": {
						"type": "array",
						"items": {
							"type": "object",
							"required": ["slug", "label", "date", "url"],
							"additionalProperties": false,
							"properties": {
								"slug": {"type": "string", "pattern": "^[a-z0-9]+(-[a-z0-9]+)*$"},
								"label": {"type": "string"},
								"date": {"type": ["integer", "null"]},
								"url": {"type": ["string", "null"]}
							}
						}
					}
				}
			}
		}
	}
}
```

- `labs` follows the order of `index.json`. Copy each lab's `slug` and `label` from `index.json` exactly.
- A model's `label` is its name as the lab writes it, such as `Claude Fable 5.2` or `GPT-Live-1.1`.
- A model's `slug` is its `label` in lowercase, with every run of characters other than `a-z` and `0-9` replaced by one `-`, and no `-` at the start or end: `Claude Fable 5.2` becomes `claude-fable-5-2`.
- `date` is the Unix timestamp in seconds as found in the data. Do not convert it.
- `url` is the `url` of the same item as `date`, copied exactly, or `null` when that item has no link.

Example:

```
{
	"labs": [
		{"slug": "anthropic", "label": "Anthropic", "models": [{"slug": "claude-fable-5-2", "label": "Claude Fable 5.2", "date": 1794182400, "url": "https://www.anthropic.com/news/claude-fable-5-2"}]},
		{"slug": "microsoft", "label": "Microsoft", "models": [{"slug": "mai-image-2-7", "label": "MAI Image 2.7", "date": 1794939396, "url": "https://microsoft.ai/news/mai-image-2-7/"}, {"slug": "mai-realtime-1", "label": "MAI Realtime 1", "date": 1794939377, "url": "https://microsoft.ai/news/mai-realtime-1/"}]},
		{"slug": "luma", "label": "Luma AI", "models": []}
	]
}
```
