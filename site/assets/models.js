/**
 * Models page runtime for Tech Feed.
 *
 * Read `index.json` next to the page, then the `site/latest.json` file of every
 * lab that has one (written by the Raspberry updater), and list each model as a
 * dotted-leader line grouped by the month of release, newest first. Load after
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
 * Load the latest models of every lab that has a site file.
 *
 * @returns {Promise<Array<{lab: {slug: string, label: string}, model: {slug: string, label: string, date: ?number, url: ?string}}>>} One entry per model, newest first, undated models last.
 */
async function loadModels() {
	const index = await getJson("index.json");

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

document.addEventListener("DOMContentLoaded", async () => {
	const container = document.querySelector(".months");

	if (container) {
		renderModels(container, await loadModels());
		cascade(container);
	}
});
