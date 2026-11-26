/**
 * Models page runtime for Tech Feed.
 *
 * Read `index.json` next to the page, then the `site/latest.json` file of every
 * lab that has one (written by the Raspberry updater), and list each model as a
 * dotted-leader line grouped by the month of release, newest first. The
 * "Following N labs" button opens a layer that lists every lab in the
 * repository, followed ones highlighted. Load after
 * `landing.js` (background and argument checks) and `section.js` (shared helpers).
 */

const ICONS = new Map();

/**
 * Format a Unix timestamp as a short UTC date, with the time unless it is exactly midnight.
 *
 * Sources that publish only the day are stored as midnight UTC, so a midnight
 * time carries no information and is left out.
 *
 * @param {number} seconds Unix timestamp in seconds.
 * @returns {string} Text such as "Nov 25 11:09" or "Nov 19".
 */
function formatWhen(seconds) {
	if (!Number.isInteger(seconds)) {
		throw new TypeError("seconds must be an integer");
	}

	const when = new Date(seconds * 1000);
	const day = when.toLocaleDateString("en-US", {month: "short", day: "2-digit", timeZone: "UTC"});

	if (seconds % DAY_SECONDS === 0) {
		return day;
	}

	return `${day} ${when.toLocaleTimeString("en-GB", {hour: "2-digit", minute: "2-digit", timeZone: "UTC"})}`;
}

/**
 * Create the icon of a lab. The SVG is inserted inline, so color icons keep their
 * colors and the parts drawn with `currentColor` follow the text color.
 *
 * @param {string} slug Lab slug, which is also the icon file name.
 * @returns {HTMLSpanElement} Icon element, filled once the SVG has loaded.
 */
function labIcon(slug) {
	requireText("slug", slug);

	const icon = element("span", "icon");

	icon.setAttribute("aria-hidden", "true");

	if (!ICONS.has(slug)) {
		ICONS.set(slug, fetch(`../assets/icons/${slug}.svg`).then((response) => (response.ok ? response.text() : "")).catch(() => ""));
	}

	ICONS.get(slug).then((svg) => {
		icon.innerHTML = svg;
	});

	return icon;
}

/**
 * Load the models of every lab of the index that has a site file.
 *
 * @param {?object} index Parsed `index.json`, or null when it could not be read.
 * @returns {Promise<Array<{lab: {slug: string, label: string}, model: {slug: string, label: string, date: ?number, url: ?string}}>>} One entry per model, newest first, undated models last.
 */
async function loadModels(index) {
	if (index !== null && typeof index !== "object") {
		throw new TypeError("index must be an object or null");
	}

	if (!index || !Array.isArray(index.labs)) {
		return [];
	}

	const files = await Promise.all(index.labs.map((lab) => (lab.site ? getJson(lab.site) : null)));
	const entries = [];

	files.forEach((file, position) => {

		if (!file || !Array.isArray(file.models)) {
			return;
		}

		const lab = {slug: index.labs[position].slug, label: index.labs[position].label};

		for (const model of file.models) {
			entries.push({lab, model});
		}
	});

	return entries.sort((a, b) => (b.model.date || 0) - (a.model.date || 0));
}

/**
 * Build the message shown when there are no models to list.
 *
 * @returns {HTMLDivElement} Empty state block.
 */
function emptyState() {
	const block = element("div", "empty");

	block.append(element("span", "empty-label", "The frontier is quiet"), element("p", "empty-text", "Somewhere, the next model is still training."));

	return block;
}

/**
 * Render the model lines, grouped by month, into a container.
 *
 * @param {HTMLElement} container Element that receives the month groups.
 * @param {Array<{lab: object, model: object}>} entries Models from `loadModels`.
 * @returns {void}
 */
function renderModels(container, entries) {
	requireInstance("container", container, HTMLElement);

	if (!Array.isArray(entries)) {
		throw new TypeError("entries must be an array");
	}

	container.replaceChildren();

	if (!entries.length) {
		container.append(emptyState());
		return;
	}

	let rows = null;
	let current = "";

	for (const {lab, model} of entries) {
		const month = Number.isInteger(model.date) ? monthOf(model.date) : "Undated";

		if (month !== current) {
			current = month;
			rows = element("div", "rows");
			container.append(element("div", "month", month), rows);
		}

		const row = rowElement(model.url);
		const when = Number.isInteger(model.date) ? formatWhen(model.date) : "";

		row.append(labIcon(lab.slug), element("span", "lab", lab.label), element("span", "dots"), element("span", "model", model.label), element("span", "day", when));
		rows.append(row);
	}
}

/**
 * Fill the "Following N labs" button and the chips of the Labs layer.
 *
 * The labs of the index are the followed ones; `untracked` lists the labs whose
 * scraper is in the repository but whose data is not built. All of them are
 * shown in alphabetical order. Without an index the button is removed.
 *
 * @param {?object} index Parsed `index.json`, or null when it could not be read.
 * @returns {void}
 */
function renderLabs(index) {
	if (index !== null && typeof index !== "object") {
		throw new TypeError("index must be an object or null");
	}

	const trigger = document.querySelector(".labs-trigger");
	const chips = document.querySelector(".labs-layer .chips");

	if (!trigger || !chips) {
		return;
	}

	if (!index || !Array.isArray(index.labs)) {
		trigger.closest(".following").remove();
		return;
	}

	const followed = index.labs.map(({slug, label}) => ({slug, label, on: true}));
	const others = Array.isArray(index.untracked) ? index.untracked.map(({slug, label}) => ({slug, label, on: false})) : [];
	const labs = followed.concat(others).sort((a, b) => a.label.localeCompare(b.label, "en", {sensitivity: "base"}));

	labs.forEach((lab, position) => {
		const chip = element("span", lab.on ? "chip on" : "chip");

		chip.style.setProperty("--k", position);
		chip.append(labIcon(lab.slug), element("span", "", lab.label));
		chips.append(chip);
	});

	trigger.textContent = `${followed.length} labs`;
	trigger.closest(".following").classList.remove("pending");
}

/**
 * Open or close the Labs layer, moving the focus into it and back to the button.
 *
 * @param {boolean} open Whether the layer is shown.
 * @returns {void}
 */
function setLabsOpen(open) {
	if (typeof open !== "boolean") {
		throw new TypeError("open must be a boolean");
	}

	const trigger = document.querySelector(".labs-trigger");
	const layer = document.querySelector(".labs-layer");

	if (!trigger || !layer || layer.classList.contains("open") === open) {
		return;
	}

	layer.classList.toggle("open", open);
	trigger.setAttribute("aria-expanded", String(open));

	(open ? layer : trigger).focus({preventScroll: true});
}

/**
 * Attach the listeners of the Labs layer: the button toggles it, and Escape or a click anywhere but a link closes it.
 *
 * @returns {void}
 */
function bindLabs() {
	const trigger = document.querySelector(".labs-trigger");
	const layer = document.querySelector(".labs-layer");

	if (!trigger || !layer) {
		return;
	}

	trigger.addEventListener("click", () => setLabsOpen(trigger.getAttribute("aria-expanded") !== "true"));

	layer.addEventListener("click", (event) => {

		if (!event.target.closest("a")) {
			setLabsOpen(false);
		}
	});

	document.addEventListener("keydown", (event) => {

		if (event.key === "Escape") {
			setLabsOpen(false);
		}
	});
}

document.addEventListener("DOMContentLoaded", async () => {
	const container = document.querySelector(".months");
	const index = await getJson("index.json");

	bindLabs();
	renderLabs(index);

	if (container) {
		renderModels(container, await loadModels(index));
		cascade(container);
	}
});
