# Sakib Grotesk source

Newly drawn reconstruction study after Söhne Buch by Kris Sowersby / Klim Type Foundry. Reference: https://klim.co.nz/fonts/soehne/

With Python 3, fonttools and brotli installed:

```
python3 _data/typeface/build_font.py
```

The variable TTF/WOFF2 and static cuts are written to `build/` beside this file. Copy only `SakibGrotesk-Regular.woff2` into `assets/fonts/` with a new versioned name, then update the shared CSS, page preloads and `_data/build.py` template together.

Only static Regular 400 is supported on the site, reserved for large titles. Use Schibsted Grotesk for reading text and small labels. The source also emits experimental 400–650 variable and heavier static files; do not deploy them. Disable synthetic bolding when using Regular. No italic, Arabic or manual hinting. The site deliberately uses Schibsted Grotesk for true italic and missing Latin characters, and Amiri for Arabic. The public type notes live in `/craft/`.
