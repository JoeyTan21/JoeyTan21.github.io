# JoeyTan21.github.io

Personal website of Joey Tan. Plain HTML/CSS; the only build step is a Python
script that pulls open-source stats from the GitHub API before deploy.

## Structure

```
index.html           # Home: name, tagline, contact links
experience/index.html # Work experience, education, skills — mirrors the resume
projects/index.html  # Projects list — edit the <article class="entry"> blocks
open-source/index.html # Open-source PRs: stats + repo list generated, featured entries by hand, table generated
scripts/fetch_open_source.py # Fetches merged PRs + repo stars from GitHub, caches to data/, renders both pages
scripts/update_prs.py  # Regenerates the PR table (needs `gh`); add PRs to its PRS list
data/open-source.json  # Cached API snapshot; the build falls back to it if GitHub is unreachable
.github/workflows/deploy.yml # Runs the fetch script, then deploys to Pages (push to main + daily cron)
reading/index.html   # Reading list — newest first, add new <li> items at the top
styles.css           # All styling (Swiss B/W, edit CSS variables at top)
```

## Refreshing open-source stats

```sh
python3 scripts/fetch_open_source.py            # fetch from GitHub, update data/open-source.json, render HTML
python3 scripts/fetch_open_source.py --offline  # render from the cached JSON only
```

The deploy workflow runs this on every push and once a day, so the live site
stays current without commits. Commit the refreshed JSON when you want the
cached fallback to catch up. `GITHUB_TOKEN` is optional locally (higher rate limit).

## Updating the PR table

```sh
python3 scripts/update_prs.py   # refetches each PR's state via gh and rewrites open-source/index.html
```

## Local preview

```sh
python3 -m http.server 8000
# open http://localhost:8000
```

(Don't open the files directly with `file://` — links use absolute paths like `/projects/`.)

## Deployment

Hosted with GitHub Pages at <https://joeytan21.github.io>, deployed by
`.github/workflows/deploy.yml` (Settings → Pages → Source must be "GitHub Actions").
Every push to `main` and a daily schedule rebuild and redeploy the site.
