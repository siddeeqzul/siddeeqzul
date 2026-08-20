#!/usr/bin/env python3
"""
Regenerate generated/contribution-graph.svg from real GitHub contribution
data (public + private repos both included, since it reads via `gh api`
under your own authenticated session).

Usage:
    python3 generate-contribution-graph.py [github-username]

Requires: `gh` CLI, already authenticated (`gh auth status`).
Run this whenever you want to refresh the graph, then commit + push the
result — it's a static snapshot, not auto-updating.
"""
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone

USERNAME = sys.argv[1] if len(sys.argv) > 1 else "siddeeqzul"

now = datetime.now(timezone.utc)
one_year_ago = now - timedelta(days=365)

query = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays { date contributionCount color weekday }
        }
      }
    }
  }
}
"""

result = subprocess.run(
    [
        "gh", "api", "graphql",
        "-f", f"query={query}",
        "-f", f"login={USERNAME}",
        "-f", f"from={one_year_ago.isoformat()}",
        "-f", f"to={now.isoformat()}",
    ],
    capture_output=True, text=True, check=True,
)
data = json.loads(result.stdout)
cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
weeks = cal["weeks"]
total = cal["totalContributions"]

CELL, GAP, LEFT_PAD, TOP_PAD = 11, 3, 30, 30
width = LEFT_PAD + len(weeks) * (CELL + GAP)
height = TOP_PAD + 7 * (CELL + GAP) + 20

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

month_labels = []
last_month = None
for wi, week in enumerate(weeks):
    first_day = week["contributionDays"][0] if week["contributionDays"] else None
    if not first_day:
        continue
    month = first_day["date"][:7]
    if month != last_month:
        month_labels.append((wi, MONTHS[int(first_day["date"][5:7]) - 1]))
        last_month = month

svg = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
    f'viewBox="0 0 {width} {height}" font-family="Helvetica, Arial, sans-serif">',
    f'<rect width="{width}" height="{height}" fill="#0d1117" rx="6"/>',
]
for wi, label in month_labels:
    x = LEFT_PAD + wi * (CELL + GAP)
    svg.append(f'<text x="{x}" y="14" font-size="10" fill="#8b949e">{label}</text>')

for wi, week in enumerate(weeks):
    for day in week["contributionDays"]:
        x = LEFT_PAD + wi * (CELL + GAP)
        y = TOP_PAD + day["weekday"] * (CELL + GAP)
        count = day["contributionCount"]
        svg.append(
            f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{day["color"]}">'
            f"<title>{count} contribution{'s' if count != 1 else ''} on {day['date']}</title></rect>"
        )

svg.append(
    f'<text x="{LEFT_PAD}" y="{height - 6}" font-size="11" fill="#c9d1d9">'
    f"{total} contributions in the last year (public + private)</text>"
)
svg.append("</svg>")

with open("generated/contribution-graph.svg", "w") as f:
    f.write("\n".join(svg))

print(f"Wrote generated/contribution-graph.svg — {total} contributions")
