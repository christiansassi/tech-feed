"""List of the tracked security conferences and the page read for each one.

The page is the home of the conference, whose layout stays the same from one
edition to the next, except for three sites whose dates live elsewhere (a
Markdown file, a data file, a calendar feed). ``note`` tells the analysis which
edition counts when a conference runs several. Conferences that are suspended
or whose site cannot be read without a browser are not followed: ``UNTRACKED``
names them, so the page can list them as not followed.
"""

from dataclasses import dataclass

@dataclass(frozen=True)
class Conference:
	"""One tracked conference.

	Attributes:
		slug (str): Folder name in the published site, lowercase with hyphens.
		label (str): Name shown on the page.
		url (str): Page fetched every hour.
		note (str | None): Hint for the analysis, such as which edition to report.
		tickets (str | None): Ticket page to read when the fetched page does not link to it.
		home (str | None): Home page linked from the site when ``url`` is not one (a calendar feed, a data file); None means ``url``.
	"""

	slug: str
	label: str
	url: str
	note: str | None = None
	tickets: str | None = None
	home: str | None = None

CONFERENCES = [
	Conference("area41", "AREA41", "https://area41.io/"),
	Conference("balccon", "BalCCon", "https://balccon.org/"),
	Conference("botconf", "Botconf", "https://www.botconf.eu/"),
	Conference("brucon", "BruCON", "https://www.brucon.org/", "The page may omit the year: use the next dates that fall after today."),
	Conference("bsides-athens", "BSides Athens", "https://www.bsidesath.gr/"),
	Conference("bsides-krakow", "BSides Kraków", "https://bsideskrakow.pl/"),
	Conference("bsides-lisbon", "BSides Lisbon", "https://bsideslisbon.org/"),
	Conference("bsides-ljubljana", "BSides Ljubljana", "https://bsidesljubljana.si/"),
	Conference("bsides-london", "BSides London", "https://bsides.london/"),
	Conference("bsides-luxembourg", "BSides Luxembourg", "https://bsides.lu/"),
	Conference("bsides-munich", "BSides Munich", "https://www.bsidesmunich.org/"),
	Conference("bsides-prague", "BSides Prague", "https://bsides.cz/"),
	Conference("bsides-vienna", "BSides Vienna", "https://bsidesvienna.at/"),
	Conference("cansecwest", "CanSecWest", "https://www.secwest.net/"),
	Conference("ccc", "Chaos Communication Congress", "https://events.ccc.de/", "Report only the Chaos Communication Congress, not other CCC events."),
	Conference("code-blue", "CODE BLUE", "https://codeblue.jp/en/"),
	Conference("confidence", "CONFidence", "https://confidence-conference.org/"),
	Conference("cybersec-europe", "Cybersec Europe", "https://www.cyberseceurope.com/"),
	Conference("cybertech-europe", "Cybertech Europe", "https://italy.cybertechconference.com/"),
	Conference("cyberthreat", "CyberThreat", "https://cyberthreat.io/"),
	Conference("cyberuk", "CYBERUK", "https://www.cyberuk.uk/"),
	Conference("deepsec", "DeepSec", "https://deepsec.net/"),
	Conference("defcamp", "DefCamp", "https://def.camp/"),
	Conference("defcon", "DEF CON", "https://defcon.org/", "Report only DEF CON in Las Vegas, not DEF CON Singapore or DEF CON Training events."),
	Conference("defcon-singapore", "DEF CON Singapore", "https://defcon.org/", "Report only DEF CON Singapore, not DEF CON in Las Vegas or DEF CON Training events."),
	Conference("disobey", "Disobey", "https://disobey.fi/"),
	Conference("districtcon", "DistrictCon", "https://www.districtcon.org/"),
	Conference("ekoparty", "Ekoparty", "https://ekoparty.org/"),
	Conference("european-cyber-week", "European Cyber Week", "https://www.european-cyber-week.eu/"),
	Conference("euskalhack", "EuskalHack Security Congress", "https://securitycongress.euskalhack.org/"),
	Conference("forum-incyber", "Forum InCyber Europe", "https://europe.forum-incyber.com/", "Report only the Europe edition in Lille."),
	Conference("fwd-cloudsec-eu", "fwd:cloudsec Europe", "https://fwdcloudsec.org/", "Report only the Europe edition, not North America."),
	Conference("fwd-cloudsec-na", "fwd:cloudsec North America", "https://fwdcloudsec.org/", "Report only the North America edition, not Europe."),
	Conference("grehack", "GreHack", "https://grehack.fr/"),
	Conference("hackinbo", "HackInBo", "https://tickets.hackinbo.it/events/ical/?locale=en", "The page is a calendar feed. The Business and Classic editions on consecutive days form one edition: report both days.", "https://tickets.hackinbo.it/", home="https://www.hackinbo.it/"),
	Conference("hacklu", "Hack.lu", "https://hack.lu/"),
	Conference("hacktivity", "Hacktivity", "https://hacktivity.com/"),
	Conference("hardwear-io", "hardwear.io Netherlands", "https://hardwear.io/", "Report only the Netherlands edition, not the USA one."),
	Conference("hardwear-io-usa", "hardwear.io USA", "https://hardwear.io/", "Report only the USA edition, not the Netherlands one."),
	Conference("hexacon", "Hexacon", "https://www.hexacon.fr/"),
	Conference("hope", "HOPE", "https://www.hope.net/"),
	Conference("infosecurity-europe", "Infosecurity Europe", "https://www.infosecurityeurope.com/"),
	Conference("insomnihack", "Insomni'hack", "https://www.insomnihack.ch/"),
	Conference("international-cyber-expo", "International Cyber Expo", "https://www.internationalcyberexpo.com/"),
	Conference("it-sa", "it-sa Expo&Congress", "https://www.itsa365.de/en/it-sa-expo", "Use the dates in the visible text; structured data on this page can be stale."),
	Conference("kawaiicon", "Kawaiicon", "https://kawaiicon.org/"),
	Conference("lehack", "leHACK", "https://lehack.org/"),
	Conference("m0lecon", "m0leCon", "https://m0lecon.it/"),
	Conference("no-hat", "No Hat", "https://www.nohat.it/"),
	Conference("northsec", "NorthSec", "https://nsec.io/", "Report the conference days, not the training days before them."),
	Conference("nullcon-berlin", "Nullcon Berlin", "https://nullcon.net/", "Report only the Berlin edition, not Goa."),
	Conference("nullcon-goa", "Nullcon Goa", "https://nullcon.net/", "Report only the Goa edition, not Berlin."),
	Conference("offensivecon", "OffensiveCon", "https://www.offensivecon.org/", "Report only the Berlin edition, not Tokyo."),
	Conference("one-conference", "ONE Conference", "https://one-conference.nl/"),
	Conference("owasp-appsec-eu", "OWASP Global AppSec EU", "https://owasp.org/assets/sitedata/events.yml", "The page lists every OWASP event: report only Global AppSec EU. Its listed range covers three training days followed by two conference days: report only the last two days.", home="https://owasp.org/events/"),
	Conference("owasp-appsec-us", "OWASP Global AppSec USA", "https://owasp.org/assets/sitedata/events.yml", "The page lists every OWASP event: report only Global AppSec USA. Its listed range covers three training days followed by two conference days: report only the last two days.", home="https://owasp.org/events/"),
	Conference("pass-the-salt", "Pass the SALT", "https://www.pass-the-salt.org/"),
	Conference("poc", "POC", "https://powerofcommunity.net/"),
	Conference("rootedcon", "RootedCON", "https://rootedcon.com/", "Report only RootedCON Madrid."),
	Conference("rsac", "RSAC Conference", "https://www.rsaconference.com/usa", "Report only the RSAC Conference in San Francisco."),
	Conference("saintcon", "SAINTCON", "https://saintcon.org/"),
	Conference("sec-t", "SEC-T", "https://sec-t.org/"),
	Conference("security-fest", "Security Fest", "https://securityfest.com/"),
	Conference("sstic", "SSTIC", "https://www.sstic.org/"),
	Conference("steelcon", "SteelCon", "https://www.steelcon.info/"),
	Conference("sthack", "Sthack", "https://sthack.fr/"),
	Conference("swiss-cyber-storm", "Swiss Cyber Storm", "https://www.swisscyberstorm.com/"),
	Conference("troopers", "TROOPERS", "https://troopers.de/"),
	Conference("virus-bulletin", "Virus Bulletin", "https://www.virusbulletin.com/conference/"),
	Conference("x33fcon", "x33fcon", "https://www.x33fcon.com/conference.md"),
]

# Conferences left out on purpose, with their home page, shown as not followed so nobody asks for them in an issue.
UNTRACKED = [
	("Black Hat Europe", "https://www.blackhat.com/"),  # The site sits behind Cloudflare and answers 403.
	("Black Hat USA", "https://www.blackhat.com/"),  # Same site as Black Hat Europe: Cloudflare often answers 403.
	("BSides Barcelona", "https://bsides.barcelona/"),  # The dates are only in the JavaScript of the page, not in its HTML.
	("BSides Las Vegas", "https://bsideslv.org/"),  # The page is built by JavaScript and has no dates in its HTML.
	("BSides SF", "https://bsidessf.org/"),  # The page is built by JavaScript and has no dates in its HTML.
	("BSides Zürich", "https://bsideszh.ch/"),  # No conference since 2024, only meetups.
	("HITB Amsterdam", "https://conference.hitb.org/"),  # No Amsterdam edition since 2023.
	("HITB SecConf", "https://conference.hitb.org/"),  # The site answers 503 behind a bot filter.
	("LABScon", "https://www.labscon.io/"),  # The site answers 429 to automated requests.
	("Objective by the Sea", "https://objectivebythesea.org/"),  # The page is built by JavaScript and has no dates in its HTML.
	("Paranoia Oslo", None),  # The domain is gone; the last edition was in 2023.
	("REcon", "https://recon.cx/"),  # The page is built by JavaScript and has no dates in its HTML.
	("RomHack", "https://romhack.io/"),  # The conference is suspended indefinitely.
	("SecTor", "https://www.blackhat.com/sector/"),  # Same site as Black Hat Europe: Cloudflare often answers 403.
	("TyphoonCon", "https://typhooncon.com/"),  # The home page gives no dates.
	("Wild West Hackin' Fest", "https://wildwesthackinfest.com/"),  # The home page gives no dates.
	("x33fcon", "https://www.x33fcon.com/"),  # The page is built by JavaScript and has no text in its HTML.
]
