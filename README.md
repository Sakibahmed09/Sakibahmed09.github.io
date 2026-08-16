# sakib.page

Personal site. Paper, ink and one red biro.

No framework, no build step for the reader. Static HTML, one stylesheet, one script.
The venture pages are generated from a small Python script so they can refresh themselves.

## Run it locally

```bash
python3 -m http.server 5177
```

Then open http://localhost:5177/

## Pages

- `/` — the front page
- `/ventures/` — Mains (MiniDeed, Simply Smashed, PSK, Draper) and Sides
- `/ventures/<slug>/` — generated. Retrospective spine with real posts pasted in at the dates they happened
- `/chapters/` — the story, start to now
- `/craft/` — type, colour, motion decisions

## The venture pages

Each one shows **what I say about it now** next to **what I was actually posting at the time**.

Data comes from two places already on disk:

- X archive: `~/Downloads/twitter-*/data/tweets.js`
- LinkedIn cache: `~/.linkedin-cache/posts.db`. Current handle `mertesakib`; posts from
  before Aug 2026 are filed under the old `sakib-ahmed1` handle, and `mine.py` reads both.
  Existing post URLs keep the old slug on purpose: LinkedIn pins a post URL to the handle
  you had when you posted it, and rewriting them to the new slug 404s (verified).

Three files in `_data/` drive it:

| File | Job |
| --- | --- |
| `mine.py` | Reads both sources, buckets posts per venture, writes `buckets.json` |
| `ventures.json` | The curated spine. My retrospective text, and which posts sit under each beat |
| `build.py` | Matches each beat to a real post, writes the pages, and builds the self-updating lanes |

Each venture page ends with **Lately**: everything in that bucket not used in the spine,
newest first. The front page has its own **Lately** drawn from the whole corpus, injected
between the `LATELY:START/END` markers in `index.html`. Cross-posts (same story on X and
LinkedIn) collapse to whichever version travelled further.

To rebuild after editing `ventures.json`:

```bash
cd _data && python3 build.py
```

Posts are matched by a text snippet, not an ID, so the spine survives a re-scrape.
`build.py` prints anything it could not match rather than failing silently.

## Weekly refresh

`_data/refresh.sh` tops up the LinkedIn cache, re-mines, regenerates and commits.
The curated spine is never overwritten.

To install the Monday 7am job:

```bash
cp ~/claude-experiments/sakib-site/_data/com.sakib.site-refresh.plist ~/Library/LaunchAgents/ && launchctl load ~/Library/LaunchAgents/com.sakib.site-refresh.plist
```

It commits locally until the repo has a remote, then it pushes too. Log at `_data/refresh.log`.

## Deploy (GitHub Pages)

Push to a repo, then Settings → Pages → deploy from `main` / root.
As `Sakibahmed09/sakibahmed09.github.io` it serves at the root domain.
For a custom domain, add a `CNAME` file.

## Details worth knowing

- `⌘K` command palette · `t` counts the tasbih (33 completes the ring) · footer clock is always Europe/London
- Theme: system by default, moon toggle persists, `?theme=dark|light` forces it per link
- Margin notes (`aside.pen-note`) draw in on scroll, and go inline below 1180px
- Type: Schibsted Grotesk, EB Garamond italic, Reenie Beanie, Amiri
- Motion: `--swift` 160ms, `--settle` 340ms, `--grand` 700ms, reduced-motion respected
