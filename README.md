# sakib.page

Personal site. Paper, ink and one red biro.

No framework, no build step, no analytics. Four HTML files, one stylesheet, one script.

## Run it locally

```bash
python3 -m http.server 5177
```

Then open http://localhost:5177/

## Deploy (GitHub Pages)

Push this folder to a repo, then Settings → Pages → deploy from `main` / root.

- As `Sakibahmed09/sakibahmed09.github.io` it becomes the root site: `https://sakibahmed09.github.io/`
- As a project repo it lives at `/repo-name/` (the 404 page's absolute links assume root; adjust if using a subpath).

For a custom domain, add a `CNAME` file with the domain in it.

## Details worth knowing

- `⌘K` command palette · `t` counts the tasbih (33 completes the ring) · footer clock is always Europe/London
- Theme: system by default, moon toggle persists to localStorage, `?theme=dark|light` forces it per-link
- Margin notes (`aside.pen-note`) draw in on scroll; below 1180px they render inline
- Fonts: General Sans (Fontshare), Fraunces italic + Nanum Pen Script + Amiri (Google)
- Motion tokens: `--swift` 160ms, `--settle` 340ms, `--grand` 760ms; reduced-motion respected
