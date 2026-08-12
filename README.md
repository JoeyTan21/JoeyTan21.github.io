# Kay21T.github.io

Personal website of Joey Tan. Plain HTML/CSS, no build step.

## Structure

```
index.html           # Home: name, tagline, contact links
projects/index.html  # Projects list — edit the <article class="entry"> blocks
reading/index.html   # Reading list — edit the <li> items
styles.css           # All styling (Swiss B/W, edit CSS variables at top)
```

## Local preview

```sh
python3 -m http.server 8000
# open http://localhost:8000
```

(Don't open the files directly with `file://` — links use absolute paths like `/projects/`.)

## Deploy to GitHub Pages

1. Create a **public** repo named exactly `Kay21T.github.io` on GitHub.
2. Push this folder to its `main` branch:

   ```sh
   git init
   git add .
   git commit -m "Initial site"
   git remote add origin https://github.com/Kay21T/Kay21T.github.io.git
   git push -u origin main
   ```

3. On GitHub: Settings → Pages → Source should already be `main` / root.
   The site goes live at <https://kay21t.github.io> within a minute or two.

Any push to `main` redeploys automatically.
