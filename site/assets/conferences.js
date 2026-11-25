/**
 * Conferences page runtime for Tech Feed.
 *
 * Read `index.json` next to the page, then the `site/latest.json` file of every
 * conference (written by the Raspberry updater), keep the editions that have not
 * ended, and list them as dotted-leader lines grouped by the month they start,
 * soonest first. When there is nothing to list, show the message already in the
 * page. Load after `landing.js` and `section.js`.
 */

const TICKET_TAGS = {
	available: "Tickets",
	sold_out: "Sold out",
	not_yet: "Soon",
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
 * @returns {Promise<Array<{label: string, edition: {start: number, end: number, place: ?string, url: ?string, tickets: {status: string, url: ?string}}}>>} One entry per edition that has not ended, soonest first.
 */
async function loadConferences() {
	const index = await getJson("index.json");

	if (!index || !Array.isArray(index.conferences)) {
		return [];
	}

	const files = await Promise.all(index.conferences.map((conference) => getJson(conference.site)));
	const today = Math.floor(Date.now() / 1000 / DAY_SECONDS) * DAY_SECONDS;

	return files
		.filter((file) => file && file.edition && Number.isInteger(file.edition.end) && file.edition.end >= today)
		.map((file) => ({label: file.label, edition: file.edition}))
		.sort((a, b) => a.edition.start - b.edition.start);
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

	for (const {label, edition} of entries) {
		const month = monthOf(edition.start);

		if (month !== current) {
			current = month;
			rows = element("div", "rows");
			container.append(element("div", "month", month), rows);
		}

		const row = rowElement(edition.url);
		const tag = TICKET_TAGS[edition.tickets && edition.tickets.status] || "";

		row.classList.add("event");
		row.append(element("span", "model", label), element("span", "dots"), element("span", "lab", edition.place || ""), element("span", "day", formatDays(edition.start, edition.end)), element("span", `tag tag-${edition.tickets ? edition.tickets.status : "unknown"}`, tag));
		rows.append(row);
	}
}

document.addEventListener("DOMContentLoaded", async () => {
	const container = document.querySelector(".months");

	if (container) {
		renderConferences(container, await loadConferences());
	}
});
