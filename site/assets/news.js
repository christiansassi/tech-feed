/**
 * News page runtime for Tech Feed.
 *
 * Read `index.json` next to the page for the update time and the list of
 * sources, then `site/latest.json` (written by the Raspberry updater after the
 * Codex filters) for the items of the last 24 hours, and show each item as a
 * card: a generated cover from `covers.js`, the title (amber and bold for HOT
 * items), the time in the visitor's time zone and the source. A click flips the
 * card to its back, with the intro of the article and the link to it. The All / Hot
 * filter above the cards hides the items that are not HOT. Load after
 * `landing.js`, `section.js`, `cover-styles.js` and `covers.js`.
 */

/**
 * Return the date and time of a Unix timestamp in the visitor's time zone, such as "Nov 26, 09:50".
 *
 * @param {number} seconds Unix timestamp in seconds.
 * @returns {string} Short month, day and 24-hour time.
 */
function formatMoment(seconds) {
	if (!Number.isInteger(seconds)) {
		throw new TypeError("seconds must be an integer");
	}

	const when = new Date(seconds * 1000);
	const day = when.toLocaleDateString("en-US", {month: "short", day: "numeric"});
	const time = when.toLocaleTimeString("en-GB", {hour: "2-digit", minute: "2-digit"});

	return `${day}, ${time}`;
}

/**
 * Load the items of the site file named by the index.
 *
 * @param {?object} index Parsed `index.json`, or null when it could not be read.
 * @returns {Promise<Array<{id: string, title: string, source: string, url: string, date: number, hot: boolean, summary: ?string}>>} Valid items, newest first.
 */
async function loadNews(index) {
	if (index !== null && typeof index !== "object") {
		throw new TypeError("index must be an object or null");
	}

	const file = await getJson(index && typeof index.site === "string" ? index.site : "site/latest.json");

	if (!file || !Array.isArray(file.items)) {
		return [];
	}

	return file.items
		.filter((item) => item && typeof item.title === "string" && typeof item.url === "string" && Number.isInteger(item.date))
		.sort((a, b) => b.date - a.date);
}

/**
 * Return the intro of an item when it says something, or null; feeds such as Hacker News only give "Comments".
 *
 * @param {*} summary Intro text from the site file.
 * @returns {?string} Trimmed intro of at least 40 characters, or null.
 */
function usableIntro(summary) {
	return typeof summary === "string" && summary.trim().length >= 40 ? summary.trim() : null;
}

/**
 * Build the card of one item: the front shows the cover, the title, the time and the source; the back shows the intro over the darkened cover and the link to the article.
 *
 * @param {{title: string, source: string, url: string, date: number, hot: boolean, summary: ?string}} item News item.
 * @param {number} position Position of the card, used for the entrance delay.
 * @returns {HTMLElement} Card that flips when clicked.
 */
function newsCard(item, position) {
	if (!item || typeof item.url !== "string") {
		throw new TypeError("item must have a url");
	}

	if (!Number.isInteger(position) || position < 0) {
		throw new RangeError("position must be a non-negative integer");
	}

	const hot = item.hot ? " is-hot" : "";
	const card = element("div", `flip-card${hot}`);
	const inner = element("div", "inner");
	const front = element("div", `face front card${hot}`);
	const back = element("div", "face back");
	const art = element("div", "art");
	const image = element("img", "");
	const foot = element("div", "foot");
	const source = element("span", "source", item.source || "");
	const read = element("a", "read", `Read on ${item.source || "the source"}`);
	const intro = usableIntro(item.summary);

	card.tabIndex = 0;
	card.setAttribute("role", "button");
	card.setAttribute("aria-pressed", "false");
	card.style.setProperty("--j", position);
	image.alt = "";
	source.title = item.source || "";
	read.href = item.url;
	read.target = "_blank";
	read.rel = "noopener";

	image.addEventListener("load", () => image.classList.add("ready"), {once: true});
	coverUrl(item.url).then((url) => {
		image.src = url;
		back.style.backgroundImage = `url(${url})`;
	}).catch((error) => console.warn("Cover not drawn:", error));

	art.append(image);
	foot.append(element("span", "when", formatMoment(item.date)), source);
	front.append(art, element("h3", "", item.title), foot);
	back.append(element("h3", "", item.title), element("p", "intro", intro || "This source gives no intro: open the article to read it."), read);
	inner.append(front, back);
	card.append(inner);

	return card;
}

/**
 * Flip a card to its back or its front.
 *
 * @param {HTMLElement} card A `.flip-card`.
 * @param {boolean} flipped Whether the back is shown.
 * @returns {void}
 */
function setFlipped(card, flipped) {
	requireInstance("card", card, HTMLElement);

	if (typeof flipped !== "boolean") {
		throw new TypeError("flipped must be a boolean");
	}

	card.classList.toggle("flipped", flipped);
	card.setAttribute("aria-pressed", String(flipped));
}

/**
 * Attach the flip listeners: a click or Enter flips a card and turns the others back, Escape turns every card back; the link on the back opens the article.
 *
 * @param {HTMLElement} grid Element that holds the cards.
 * @returns {void}
 */
function bindFlips(grid) {
	requireInstance("grid", grid, HTMLElement);

	grid.addEventListener("click", (event) => {
		const card = event.target.closest(".flip-card");

		if (!card || event.target.closest(".read")) {
			return;
		}

		const flip = !card.classList.contains("flipped");

		grid.querySelectorAll(".flip-card.flipped").forEach((other) => other !== card && setFlipped(other, false));
		setFlipped(card, flip);
	});

	grid.addEventListener("keydown", (event) => {
		const card = event.target.closest(".flip-card");

		if (card && !event.target.closest(".read") && (event.key === "Enter" || event.key === " ")) {
			event.preventDefault();
			card.click();
		}
	});

	document.addEventListener("keydown", (event) => {

		if (event.key === "Escape") {
			grid.querySelectorAll(".flip-card.flipped").forEach((card) => setFlipped(card, false));
		}
	});
}

/**
 * Show the cards, or the empty message when there is nothing to show.
 *
 * @param {HTMLElement} grid Element that receives the cards.
 * @param {Array<object>} items Items from `loadNews`.
 * @returns {void}
 */
function renderNews(grid, items) {
	requireInstance("grid", grid, HTMLElement);

	if (!Array.isArray(items)) {
		throw new TypeError("items must be an array");
	}

	if (!items.length) {
		document.querySelector(".empty").hidden = false;
		return;
	}

	items.forEach((item, position) => grid.append(newsCard(item, position)));
	grid.classList.add("cascade");
	bindFlips(grid);
}

/**
 * Return the chips of the Following layer: one per publisher, all followed.
 *
 * @param {?object} index Parsed `index.json`, or null when it could not be read.
 * @returns {?Array<{label: string, on: boolean, icon: null}>} One entry per publisher, or null without an index.
 */
function sourceEntries(index) {
	if (index !== null && typeof index !== "object") {
		throw new TypeError("index must be an object or null");
	}

	if (!index || !Array.isArray(index.sources)) {
		return null;
	}

	const labels = [...new Set(index.sources.map((source) => source.label).filter((label) => typeof label === "string"))];

	return labels.map((label) => ({label, on: true, icon: null}));
}

/**
 * Move the thumb of the All / Hot filter under one option.
 *
 * @param {HTMLElement} filter The `.news-filter` element.
 * @param {HTMLButtonElement} button Option the thumb moves to.
 * @param {boolean} animate Whether the move is animated; false places it at once.
 * @returns {void}
 */
function placeThumb(filter, button, animate) {
	requireInstance("filter", filter, HTMLElement);
	requireInstance("button", button, HTMLButtonElement);

	if (typeof animate !== "boolean") {
		throw new TypeError("animate must be a boolean");
	}

	const left = button.offsetLeft;
	const forward = left > Number.parseFloat(filter.style.getPropertyValue("--left") || "0");

	filter.classList.toggle("still", !animate);

	// The edge on the side of the move leaves first and the other follows.
	filter.style.setProperty("--left-delay", forward ? "0.08s" : "0s");
	filter.style.setProperty("--right-delay", forward ? "0s" : "0.08s");
	filter.style.setProperty("--left", `${left}px`);
	filter.style.setProperty("--right", `${filter.clientWidth - left - button.offsetWidth}px`);

	if (!animate) {
		void filter.offsetWidth;
		filter.classList.remove("still");
	}
}

/**
 * Reserve the place of the All / Hot filter when some item is HOT and attach its listeners; it stays invisible until `revealFilter`.
 *
 * @param {Array<object>} items Items from `loadNews`.
 * @returns {?HTMLElement} The filter, or null when no item is HOT.
 */
function bindNewsFilter(items) {
	if (!Array.isArray(items)) {
		throw new TypeError("items must be an array");
	}

	const filter = document.querySelector(".news-filter");

	if (!filter || !items.some((item) => item.hot)) {
		return null;
	}

	filter.hidden = false;
	filter.prepend(element("span", "thumb"));

	const active = () => filter.querySelector('button[aria-pressed="true"]');

	placeThumb(filter, active(), false);
	document.fonts.ready.then(() => placeThumb(filter, active(), false));

	filter.addEventListener("click", (event) => {
		const button = event.target.closest("button[data-filter]");

		if (!button || button === active()) {
			return;
		}

		document.body.classList.toggle("hot-only", button.dataset.filter === "hot");
		filter.querySelectorAll("button").forEach((other) => other.setAttribute("aria-pressed", String(other === button)));
		placeThumb(filter, button, true);
		replayEntrance(document.querySelector(".cards"));
	});

	return filter;
}

/**
 * Play the card entrance again on the cards left visible, numbered from the first one, after the filter changes.
 *
 * @param {HTMLElement} grid Element that holds the cards.
 * @returns {void}
 */
function replayEntrance(grid) {
	requireInstance("grid", grid, HTMLElement);

	const visible = [...grid.querySelectorAll(".flip-card")].filter((card) => getComputedStyle(card).display !== "none");

	visible.forEach((card, position) => card.style.setProperty("--j", position));
	grid.classList.remove("cascade");
	void grid.offsetWidth;
	grid.classList.add("cascade");
}

/**
 * Fade the filter in together with the first card, when its entrance starts.
 *
 * @param {HTMLElement} filter The `.news-filter` element.
 * @param {HTMLElement} grid Element that holds the cards.
 * @returns {Promise<void>} Resolves when the filter is shown.
 */
async function revealFilter(filter, grid) {
	requireInstance("filter", filter, HTMLElement);
	requireInstance("grid", grid, HTMLElement);

	const first = grid.querySelector(".card");

	if (first) {
		await Promise.all(first.getAnimations().map((animation) => animation.ready.catch(() => {})));
	}

	filter.classList.add("shown");
}

document.addEventListener("DOMContentLoaded", async () => {
	const grid = document.querySelector(".cards");
	const index = await getJson("index.json");

	bindFollowing();
	renderFollowing(sourceEntries(index), "sources");

	if (grid) {
		const items = await loadNews(index);

		const filter = bindNewsFilter(items);

		renderNews(grid, items);

		if (filter) {
			revealFilter(filter, grid);
		}
	}
});
