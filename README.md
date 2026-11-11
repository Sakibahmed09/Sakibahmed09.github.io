# sakib.lol

Personal site. A memo, with receipts. Paper, ink and one red biro.

No framework, no build step for the reader. Static HTML, one stylesheet, one script.
The venture pages are generated from a small Python script so they can refresh themselves.

## Run it locally

```bash
python3 -m http.server 5177
```

Then open http://localhost:5177/

## Pages

- `/` — the front page
- `/ventures/<slug>/` — generated, for Draper, Bilal, Simply Smashed and MiniDeed. A project marked `"page": false` in `ventures.json` keeps its write-up but gets no page, and its old address forwards. Retrospective spine with real posts pasted in at the dates they happened
- `/chapters/` — the story, start to now. Written in `_data/chapters.py`, which also pulls the receipts
- `/craft/` — type, colour, motion decisions

## The venture pages

Each one shows **what I say about it now** next to **what I was actually posting at the time**.

Data comes from two places already on disk:

- X archive: `_data/archive/tweets*.js` (gitignored; every part of the download is read, and
  the photos sit in `_data/archive/tweets_media`). It lives inside the repo on purpose: macOS
  blocks launchd jobs from reading `~/Downloads`, so a copy left there made the weekly refresh
  fail every Monday. `~/Downloads/twitter-*/data` is only a fallback for a hand-run session.
- LinkedIn cache: `~/.linkedin-cache/posts.db`. Current handle `mertesakib`; posts from
  before Aug 2026 are filed under the old `sakib-ahmed1` handle, and `mine.py` reads both.
  Existing post URLs keep the old slug on purpose: LinkedIn pins a post URL to the handle
  you had when you posted it, and rewriting them to the new slug 404s (verified).

Photos: archive tweets use the archive's own files, and a video-only tweet gets a still
from its clip. Newer tweets come from the @mertesakib timeline on fxtwitter (free, no key;
Typefully dropped its analytics feed in Sep 2026), and `pull_tweets.py` saves each one's
first photo or video still once. The same pass notices cached tweets later deleted on X,
and they drop off the site.

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

## The memo and the receipts

The front page is a memo: To, Re, Date, then numbered sections. The subject line is
"Don't stay too long in this place", so the footer of every page counts the visit and
says the line back after five minutes.

`/chapters/` is written inside `_data/chapters.py`. Every `[[key]]` in the prose is a
receipt: a line posted at the time, cut out of `buckets.json` by its first and last
words. If the words are not in the post the script stops, so a receipt can never be
misquoted. Rebuild after editing the story:

```bash
cd _data && python3 chapters.py
```

The weekly refresh does not touch this page.

Every chapter heading ends at a small door, set in `DOORS` in the same file: shut, ajar
or open, with the line it says when touched. The front page, the footer and the 404 use
the same door. Sizes other than 1:1 set their own stroke width, because the outline is
drawn with a dash and a non-scaling stroke measures that dash in screen pixels.

Other small things, all in `assets/site.js`: the memo's date is today's, the paper's warmth follows the sun where the reader
is, a Boris bike rides out of the margin once at its paragraph, and the palette has two
commands that are not pages.

## The card and the icon

`assets/og-v3.png` is the social card. Its source is `_data/card.html`: open it at
1200 by 630 and screenshot it. `assets/icon.svg` is the door icon, inlined into every page
as a data URI, with `assets/apple-touch-icon.png` for phones.

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

- `⌘K` command palette · `t` counts the tasbih (33 completes the ring) · the footer clock follows the reader's timezone
- Theme: system by default, moon toggle persists, `?theme=dark|light` forces it per link
- Receipts (`aside.receipts`) sit in the margin beside their number, and go under the paragraph below 1180px
- Pen notes (`aside.pen-note`) only write on old posts and on the craft page
- Type: Sakib Grotesk Regular (large titles), Schibsted Grotesk (body text, small headings, labels and true italic), Reenie Beanie, Amiri
- Motion: `--swift` 160ms, `--settle` 340ms, `--grand` 700ms, reduced-motion respected
