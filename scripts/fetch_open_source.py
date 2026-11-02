#!/usr/bin/env python3
"""Build-time data pipeline for the open-source showcase.

What it does, in order:

  1. Ask the GitHub REST search API for every MERGED pull request authored by
     USERNAME in repositories USERNAME does not own.
  2. Ask the search API for star counts and descriptions of those repositories
     (a few repos per request, so ~20 repos cost ~3 requests).
  3. Save the result to data/open-source.json (the committed cache).
     If any network step fails, load the cached JSON instead so the site
     still builds.
  4. Render HTML from the data and splice it into index.html and
     open-source/index.html between <!-- oss:start --> and <!-- oss:end -->.

Run from anywhere:

    python3 scripts/fetch_open_source.py            # fetch, cache, render
    python3 scripts/fetch_open_source.py --offline  # skip the API, render from cache

Set GITHUB_TOKEN for a higher rate limit (GitHub Actions provides one
automatically). Unauthenticated requests also work but are limited to
10 search calls per minute. Only the Python standard library is used.
"""
import html
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

USERNAME = "JoeyTan21"
API = "https://api.github.com"

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "data" / "open-source.json"
HOME_PAGE = ROOT / "index.html"
OSS_PAGE = ROOT / "open-source" / "index.html"

# Everything between these two comments is overwritten on each run.
MARKER = re.compile(r"(<!-- oss:start -->)(.*?)(<!-- oss:end -->)", re.S)


# ---------------------------------------------------------------- fetching

def github_get(path: str, params: dict) -> dict:
    """GET one JSON document from the GitHub REST API."""
    url = f"{API}{path}?{urllib.parse.urlencode(params)}"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": f"{USERNAME}-site-build",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:  # never hardcoded; comes from the environment only
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def fetch_merged_prs() -> list[dict]:
    """All merged PRs by USERNAME outside USERNAME's own repos.

    `-user:USERNAME` excludes repositories owned by that account (including
    forks), which is exactly the "not owned by me" rule. The search API
    returns 100 items per page, so we page until a page comes back short.
    """
    query = f"is:pr is:merged author:{USERNAME} -user:{USERNAME}"
    prs, page = [], 1
    while True:
        data = github_get("/search/issues", {"q": query, "per_page": 100, "page": page})
        items = data["items"]
        for item in items:
            if not item.get("pull_request", {}).get("merged_at"):
                continue  # belt and braces: skip anything not actually merged
            # repository_url looks like https://api.github.com/repos/owner/name
            repo = item["repository_url"].split("/repos/")[1]
            if repo.split("/")[0].lower() == USERNAME.lower():
                continue  # defensive: never count my own repos
            prs.append({
                "repo": repo,
                "number": item["number"],
                "title": item["title"],
                "url": item["html_url"],
                "merged_at": item["pull_request"]["merged_at"],
            })
        if len(items) < 100:
            return prs
        page += 1


def fetch_repo_info(repo_names: list[str]) -> dict[str, dict]:
    """Stars and description per repo, via repository search.

    One request can carry several `repo:owner/name` qualifiers, so we batch
    eight at a time instead of hitting /repos/{owner}/{name} once per repo.
    """
    info = {}
    for start in range(0, len(repo_names), 8):
        batch = repo_names[start:start + 8]
        query = " ".join(f"repo:{name}" for name in batch)
        data = github_get("/search/repositories", {"q": query, "per_page": 100})
        for item in data["items"]:
            info[item["full_name"]] = {
                "stars": item["stargazers_count"],
                "description": item["description"] or "",
                "url": item["html_url"],
            }
    return info


def build_snapshot() -> dict:
    """Combine PRs and repo metadata into the JSON shape the renderer uses."""
    prs = fetch_merged_prs()
    by_repo = defaultdict(list)
    for pr in prs:
        by_repo[pr["repo"]].append(pr)
    info = fetch_repo_info(sorted(by_repo))

    repos = []
    for name, repo_prs in by_repo.items():
        meta = info.get(name, {"stars": 0, "description": "", "url": f"https://github.com/{name}"})
        repo_prs.sort(key=lambda p: p["merged_at"], reverse=True)  # newest first
        repos.append({
            "name": name,
            "url": meta["url"],
            "stars": meta["stars"],
            "description": meta["description"],
            "prs": [{k: v for k, v in p.items() if k != "repo"} for p in repo_prs],
        })
    repos.sort(key=lambda r: r["stars"], reverse=True)  # most-starred first

    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "username": USERNAME,
        "merged_pr_count": len(prs),
        "repo_count": len(repos),
        "repos": repos,
    }


def load_snapshot(offline: bool) -> dict:
    """Fresh data if possible, otherwise the committed cache."""
    if not offline:
        try:
            snapshot = build_snapshot()
            CACHE.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n")
            print(f"fetched {snapshot['merged_pr_count']} merged PRs across "
                  f"{snapshot['repo_count']} repos; cache updated")
            return snapshot
        except Exception as error:  # network, rate limit, schema change...
            print(f"warning: GitHub API failed ({error!r}); using cached data", file=sys.stderr)
    snapshot = json.loads(CACHE.read_text())
    print(f"using cache from {snapshot['generated_at']}")
    return snapshot


# --------------------------------------------------------------- rendering

def format_stars(n: int) -> str:
    """168447 -> '168k', 9935 -> '9.9k', 744 -> '744'."""
    if n < 1_000:
        return str(n)
    if n < 10_000:
        return f"{n / 1000:.1f}".rstrip("0").rstrip(".") + "k"
    return f"{round(n / 1000)}k"


def plural(n: int, word: str) -> str:
    return f"{n} {word}" + ("" if n == 1 else "s")


def render_home_banner(data: dict) -> str:
    """One sentence for the grey card at the top of the home page."""
    top = data["repos"][0]
    return (
        f"Most of my work lives in open source — "
        f"<strong>{plural(data['merged_pr_count'], 'merged PR')}</strong> across "
        f"{plural(data['repo_count'], 'project')}, including "
        f"{html.escape(top['name'])} ⭐ {format_stars(top['stars'])} →"
    )


def render_oss_section(data: dict) -> str:
    """Headline stats plus the per-repository list for the Open Source page."""
    updated = datetime.strptime(data["generated_at"], "%Y-%m-%dT%H:%M:%SZ").strftime("%-d %b %Y")
    out = [
        "",
        '    <section class="oss-stats" aria-label="Open-source summary">',
        f'      <div class="stat"><span class="stat-num">{data["merged_pr_count"]}</span>'
        '<span class="stat-label">Merged pull requests</span></div>',
        f'      <div class="stat"><span class="stat-num">{data["repo_count"]}</span>'
        '<span class="stat-label">Projects contributed to</span></div>',
        f'      <p class="stat-note">Merged PRs to repositories I don’t own · '
        f'from the GitHub API · updated {updated}</p>',
        "    </section>",
        "",
        '    <h2 class="group-head">By repository · sorted by stars</h2>',
        "",
        '    <ul class="repo-list">',
    ]
    for repo in data["repos"]:
        links = " ".join(
            f'<a href="{pr["url"]}" target="_blank" rel="noopener" '
            f'title="{html.escape(pr["title"])}">#{pr["number"]}</a>'
            for pr in repo["prs"]
        )
        out += [
            "      <li>",
            '        <div class="repo-head">',
            f'          <a class="repo-name" href="{repo["url"]}" target="_blank" rel="noopener">'
            f'{html.escape(repo["name"])}</a>',
            f'          <span class="repo-stars">★ {format_stars(repo["stars"])}</span>',
            "        </div>",
            f'        <p class="repo-desc">{html.escape(repo["description"])}</p>',
            f'        <p class="repo-prs"><span>{plural(len(repo["prs"]), "merged PR")}</span> {links}</p>',
            "      </li>",
        ]
    out += ["    </ul>", "    "]
    return "\n".join(out)


def splice(page: Path, content: str) -> None:
    """Replace whatever sits between the oss markers in `page` with `content`."""
    src = page.read_text()
    new, count = MARKER.subn(lambda m: m.group(1) + content + m.group(3), src)
    if count != 1:
        sys.exit(f"error: expected exactly one oss:start/oss:end block in {page}, found {count}")
    page.write_text(new)
    print(f"updated {page.relative_to(ROOT)}")


def main() -> None:
    data = load_snapshot(offline="--offline" in sys.argv)
    splice(HOME_PAGE, render_home_banner(data))
    splice(OSS_PAGE, render_oss_section(data))


if __name__ == "__main__":
    main()
