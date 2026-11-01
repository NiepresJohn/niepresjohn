"""Wrap the pacman graph and render contribution stats inside animated terminal frames.

Reads dist/pacman-contribution-graph-dark.svg, writes dist/contributions-frame.svg and
dist/stats-frame.svg. Needs GITHUB_TOKEN + GITHUB_REPOSITORY_OWNER (or GH_USER) in the env.
"""
import json, os, re, urllib.request
from datetime import date, timedelta

DIST = os.environ.get("DIST", "dist")
USER = os.environ.get("GH_USER") or os.environ["GITHUB_REPOSITORY_OWNER"]
O = "#FF8000"
FONT = "font-family=\"'JetBrains Mono','Fira Code','Courier New',monospace\""
W = 900

DEFS = f"""<defs><filter id="glow" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0D1117"/><stop offset="1" stop-color="#161B22"/></linearGradient>
<linearGradient id="og" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#FF8000"/><stop offset="1" stop-color="#FFC15E"/></linearGradient>
<linearGradient id="ar" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FF8000" stop-opacity=".45"/><stop offset="1" stop-color="#FF8000" stop-opacity="0"/></linearGradient></defs>"""


def frame(h, title, inner):
    tw = len(title) * 7.4
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}">{DEFS}
<clipPath id="tp"><rect x="60" y="8" width="0" height="20"><animate attributeName="width" values="0;{tw};{tw}" keyTimes="0;.1;1" dur="9s" repeatCount="indefinite"/></rect></clipPath>
<rect x=".5" y=".5" width="{W-1}" height="{h-1}" rx="12" fill="url(#bg)" stroke="{O}" stroke-opacity=".55"><animate attributeName="stroke-opacity" values=".25;.8;.25" dur="4s" repeatCount="indefinite"/></rect>
<path d="M0 12V0h12M{W-12} 0h12v12M{W} {h-12}v12h-12M12 {h}H0v-12" fill="none" stroke="{O}" stroke-width="2.5" filter="url(#glow)"/>
<circle cx="18" cy="17" r="3.5" fill="#FF5F56"/><circle cx="31" cy="17" r="3.5" fill="#FFBD2E"/><circle cx="44" cy="17" r="3.5" fill="#27C93F"/>
<text x="60" y="21" {FONT} font-size="12" fill="{O}" font-weight="700" clip-path="url(#tp)">{title}</text>
<rect x="60" y="10" width="7" height="14" fill="{O}"><animate attributeName="x" values="60;{60+tw};{60+tw}" keyTimes="0;.1;1" dur="9s" repeatCount="indefinite"/><animate attributeName="opacity" values="1;0;1" dur=".8s" repeatCount="indefinite"/></rect>
<line x1="0" y1="32" x2="{W}" y2="32" stroke="{O}" stroke-opacity=".25"/>
<rect x="1" y="1" width="{W-2}" height="{h-2}" rx="12" fill="none" stroke="url(#og)" stroke-width="2" stroke-dasharray="60 {2*(W+h)}" filter="url(#glow)"><animate attributeName="stroke-dashoffset" from="0" to="-{2*(W+h)+60}" dur="9s" repeatCount="indefinite"/></rect>
<rect x="0" y="31" width="70" height="2" fill="url(#og)"><animate attributeName="x" values="0;{W-70};0" dur="3.5s" repeatCount="indefinite"/></rect>
{inner}</svg>"""


def pacman_frame():
    src = open(f"{DIST}/pacman-contribution-graph-dark.svg", encoding="utf-8").read()
    m = re.search(r'<svg width="(\d+)" height="(\d+)"', src)
    pw, ph = int(m.group(1)), int(m.group(2))
    body = src[src.index(">", m.end()) + 1 : src.rindex("</svg>")]
    cw = W - 40
    ch = round(cw * ph / pw)
    nested = f'<svg x="20" y="48" width="{cw}" height="{ch}" viewBox="0 0 {pw} {ph}">{body}</svg>'
    return frame(48 + ch + 20, "~/contributions.sh", nested)


def fetch_days():
    q = '{user(login:"%s"){contributionsCollection{contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}}}}' % USER
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": q}).encode(),
        headers={"Authorization": "bearer " + os.environ["GITHUB_TOKEN"], "User-Agent": "profile-frames"},
    )
    cal = json.load(urllib.request.urlopen(req))["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    days = [(date.fromisoformat(d["date"]), d["contributionCount"]) for w in cal["weeks"] for d in w["contributionDays"]]
    return cal["totalContributions"], sorted(days)


def streaks(days):
    today = date.today()
    counts = {d: c for d, c in days}
    best = run = 0
    for _, c in days:
        run = run + 1 if c else 0
        best = max(best, run)
    d = today if counts.get(today) else today - timedelta(days=1)
    cur = 0
    while counts.get(d):
        cur += 1
        d -= timedelta(days=1)
    return cur, best


def stats_frame(total, days):
    cur, best = streaks(days)
    last = [c for d, c in days if d <= date.today()][-30:]
    tiles = [("TOTAL · LAST YEAR", f"{total:,}", "contributions"), ("CURRENT STREAK", str(cur), "days"), ("LONGEST STREAK", str(best), "days")]
    tw = (W - 40 - 40) / 3
    inner = ""
    for i, (lab, val, unit) in enumerate(tiles):
        x = 20 + i * (tw + 20)
        inner += f"""<g transform="translate({x},48)"><rect width="{tw}" height="100" rx="12" fill="#0D1117" stroke="{O}" stroke-opacity=".35"/>
<text x="{tw/2}" y="26" text-anchor="middle" {FONT} font-size="11" font-weight="800" letter-spacing="2" fill="{O}">{lab}</text>
<text x="{tw/2}" y="68" text-anchor="middle" {FONT} font-size="38" font-weight="800" fill="url(#og)" filter="url(#glow)">{val}<animate attributeName="opacity" values="0;1" dur=".8s" begin="{i*.3}s" fill="freeze"/></text>
<text x="{tw/2}" y="88" text-anchor="middle" {FONT} font-size="12" fill="#8B949E">{unit}</text></g>"""
    gx, gy, gw, gh = 40, 190, W - 80, 90
    mx = max(max(last), 1)
    pts = [(gx + i * gw / (len(last) - 1), gy + gh - c / mx * gh) for i, c in enumerate(last)]
    line = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    area = line + f" L{gx+gw} {gy+gh} L{gx} {gy+gh} Z"
    grid = "".join(f'<line x1="{gx}" y1="{gy+gh*k/3}" x2="{gx+gw}" y2="{gy+gh*k/3}" stroke="{O}" stroke-opacity=".1"/>' for k in range(4))
    dots = "".join(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{O}"><animate attributeName="opacity" values="0;1" dur=".3s" begin="{1+i*.08:.2f}s" fill="freeze"/></circle>'
        for i, (x, y) in enumerate(pts)
    )
    inner += f"""<text x="20" y="176" {FONT} font-size="11" font-weight="800" letter-spacing="2" fill="{O}">ACTIVITY · LAST 30 DAYS</text>
{grid}<path d="{area}" fill="url(#ar)"><animate attributeName="opacity" values="0;1" dur="2s" begin="1s" fill="freeze"/></path>
<path d="{line}" fill="none" stroke="url(#og)" stroke-width="2.5" stroke-linejoin="round" pathLength="1" stroke-dasharray="1" filter="url(#glow)"><animate attributeName="stroke-dashoffset" from="1" to="0" dur="2.5s" fill="freeze"/></path>{dots}
<text x="{gx}" y="{gy+gh+22}" {FONT} font-size="10" fill="#8B949E">30 days ago</text><text x="{gx+gw}" y="{gy+gh+22}" text-anchor="end" {FONT} font-size="10" fill="#8B949E">today · peak {mx}/day</text>"""
    return frame(gy + gh + 38, "~/stats.sh", inner)


if __name__ == "__main__":
    open(f"{DIST}/contributions-frame.svg", "w", encoding="utf-8").write(pacman_frame())
    total, days = fetch_days()
    open(f"{DIST}/stats-frame.svg", "w", encoding="utf-8").write(stats_frame(total, days))
    print("frames written")
