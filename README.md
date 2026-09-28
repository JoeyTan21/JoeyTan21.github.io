# JoeyTan21.github.io

Personal website of Joey Tan. Plain HTML/CSS, no build step.

## Structure

```
index.html           # Home: name, tagline, contact links
experience/index.html # Work experience, education, skills — mirrors the resume
projects/index.html  # Projects list — edit the <article class="entry"> blocks
open-source/index.html # Open-source PRs: featured entries by hand, table generated
scripts/update_prs.py  # Regenerates the PR table (needs `gh`); add PRs to its PRS list
reading/index.html   # Reading list — edit the <li> items
styles.css           # All styling (Swiss B/W, edit CSS variables at top)
```

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

Hosted with GitHub Pages at <https://joeytan21.github.io>. Any push to `main` redeploys automatically.
