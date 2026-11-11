# Sakib Grotesk source

Newly drawn reconstruction study after Söhne Buch by Kris Sowersby / Klim Type Foundry. Reference: https://klim.co.nz/fonts/soehne/

With Python 3, fonttools and brotli installed:

```
python3 _data/typeface/build_font.py
```

The variable TTF/WOFF2 and static cuts are written to `build/` beside this file. Copy the WOFF2 into `assets/fonts/` with a new versioned name, then update the shared CSS, page preloads and `_data/build.py` template together.

Weight range 400–650. No italic, Arabic or manual hinting. The site deliberately uses Schibsted Grotesk for true italic and missing Latin characters, and Amiri for Arabic. The public type notes live in `/craft/`.
