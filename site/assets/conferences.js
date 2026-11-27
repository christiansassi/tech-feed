/**
 * Conferences page runtime for Tech Feed.
 *
 * Read `index.json` next to the page, then the `site/latest.json` file of every
 * conference (written by the Raspberry updater), keep the editions that have not
 * ended, and list them as dotted-leader lines grouped by the month they start,
 * soonest first. When there is nothing to list, show the message already in the
 * page. The "Following N conferences" button opens a layer (from `section.js`)
 * that lists every conference the feed checks, so a missing edition can be told
 * apart from a missing conference. Load after `landing.js` and `section.js`.
 */

const TICKET_TAGS = {
	available: "Tickets",
	sold_out: "Sold out",
};

/**
 * Format the days of an edition, such as "Feb 01-05" or "Feb 27-Mar 02".
 *
 * @param {number} start Unix timestamp of the first day, at midnight UTC.
 * @param {number} end Unix timestamp of the last day, at midnight UTC.
 * @returns {string} Short UTC date range, or one day when both are equal.
 */
function formatDays(start, end) {
	if (!Number.isInteger(start) || !Number.isInteger(end)) {
		throw new TypeError("start and end must be integers");
	}

	const first = new Date(start * 1000);
	const last = new Date(end * 1000);
	const day = (date) => date.toLocaleDateString("en-US", {day: "2-digit", timeZone: "UTC"});
	const month = (date) => date.toLocaleDateString("en-US", {month: "short", timeZone: "UTC"});

	if (start === end) {
		return `${month(first)} ${day(first)}`;
	}

	if (month(first) === month(last)) {
		return `${month(first)} ${day(first)}-${day(last)}`;
	}

	return `${month(first)} ${day(first)}-${month(last)} ${day(last)}`;
}

/**
 * Load the upcoming editions of every conference that has a site file.
 *
 * @param {?object} index Parsed `index.json`, or null when it could not be read.
 * @returns {Promise<Array<{label: string, icon: ?string, edition: {start: number, end: number, place: ?string, url: ?string, tickets: {status: string, url: ?string}}}>>} One entry per edition that has not ended, soonest first.
 */
async function loadConferences(index) {
	if (index !== null && typeof index !== "object") {
		throw new TypeError("index must be an object or null");
	}

	if (!index || !Array.isArray(index.conferences)) {
		return [];
	}

	const files = await Promise.all(index.conferences.map((conference) => getJson(conference.site)));
	const today = Math.floor(Date.now() / 1000 / DAY_SECONDS) * DAY_SECONDS;

	// The icon file sits next to the site file of its conference.
	const iconOf = (file, position) => (typeof file.icon === "string" ? index.conferences[position].site.replace(/[^/]*$/, file.icon) : null);

	return files
		.map((file, position) => (file && file.edition && Number.isInteger(file.edition.end) && file.edition.end >= today ? {label: file.label, icon: iconOf(file, position), edition: file.edition} : null))
		.filter(Boolean)
		.sort((a, b) => a.edition.start - b.edition.start);
}

/**
 * Create the icon slot of a conference row: the same square as the lab icons on Models, empty when the conference has no icon.
 *
 * @param {?string} src Path of the icon file, relative to the page, or null.
 * @returns {HTMLSpanElement} Icon element.
 */
function conferenceIcon(src) {
	if (src !== null && typeof src !== "string") {
		throw new TypeError("src must be a string or null");
	}

	const icon = element("span", "icon");

	icon.setAttribute("aria-hidden", "true");

	if (src) {
		const image = element("img", "");

		image.alt = "";
		image.src = src;
		image.draggable = false;
		image.addEventListener("load", () => toneIcon(image), {once: true});
		image.addEventListener("error", () => image.remove(), {once: true});
		icon.append(image);
	}

	return icon;
}

/**
 * Adapt a loaded favicon to the dark page: remove it when it has no visible pixels, and draw it as a light silhouette when it is dark and nearly gray, like the one-color lab icons.
 *
 * @param {HTMLImageElement} image Loaded icon image, served from the same origin as the page.
 * @returns {void}
 */
function toneIcon(image) {
	requireInstance("image", image, HTMLImageElement);

	const side = 32;
	const canvas = document.createElement("canvas");
	const context = canvas.getContext("2d", {willReadFrequently: true});

	canvas.width = side;
	canvas.height = side;

	let pixels;

	try {
		context.drawImage(image, 0, 0, side, side);
		pixels = context.getImageData(0, 0, side, side).data;
	} catch {
		return;
	}

	let visible = 0;
	let light = 0;
	let chroma = 0;

	for (let offset = 0; offset < pixels.length; offset += 4) {
		const [red, green, blue, alpha] = pixels.subarray(offset, offset + 4);

		if (alpha > 20) {
			visible += 1;
			light += (red + green + blue) / 3;
			chroma += Math.max(red, green, blue) - Math.min(red, green, blue);
		}
	}

	if (!visible) {
		image.remove();
		return;
	}

	// Only a dark, nearly gray icon (mean brightness and chroma out of 255) becomes a silhouette; a dark icon in color would lose its drawing.
	image.classList.toggle("dark", light / visible < 60 && chroma / visible < 48);
}

/**
 * Render the conference lines, grouped by starting month, into a container.
 *
 * @param {HTMLElement} container Element that receives the month groups.
 * @param {Array<{label: string, edition: object}>} entries Editions from `loadConferences`.
 * @returns {void}
 */
function renderConferences(container, entries) {
	requireInstance("container", container, HTMLElement);

	if (!Array.isArray(entries)) {
		throw new TypeError("entries must be an array");
	}

	if (!entries.length) {
		container.querySelector(".empty").hidden = false;
		return;
	}

	let rows = null;
	let current = "";

	for (const {label, icon, edition} of entries) {
		const month = monthOf(edition.start);

		if (month !== current) {
			current = month;
			rows = element("div", "rows");
			container.append(element("div", "month", month), rows);
		}

		const row = rowElement(edition.url);
		const status = edition.tickets ? edition.tickets.status : "unknown";

		const lead = element("span", "lead");

		lead.append(conferenceIcon(icon), element("span", "model", label), element("span", "dots"), element("span", "lab", edition.place || ""));
		row.classList.add("event");
		row.append(lead, element("span", "day", formatDays(edition.start, edition.end)));

		if (TICKET_TAGS[status]) {
			row.append(element("span", `tag tag-${status}`, TICKET_TAGS[status]));
		}

		rows.append(row);
	}
}

document.addEventListener("DOMContentLoaded", async () => {
	const container = document.querySelector(".months");
	const index = await getJson("index.json");
	const followed = index && Array.isArray(index.conferences) ? index.conferences.map(({label}) => ({label, on: true, icon: null})) : null;

	bindFollowing();
	renderFollowing(followed, "conferences");

	if (container) {
		renderConferences(container, await loadConferences(index));
		cascade(container);
	}
});
