# Presentation

The pitch deck (6 slides, with speaker notes in each slide file).

- **View it**: run `python -m server` from the repository root and open <http://localhost:8000/presentation/>. Arrow keys move through slides and builds, `F` toggles full screen.
- **Edit it**: change the deck in the slide tool, export it as a single HTML file, then run
  `python presentation/split_deck.py path/to/export.html`. This regenerates `index.html`, `slides/` and `assets/`.

| Path | What |
| --- | --- |
| `index.html` | Shell page: lists the slide files and loads them |
| `slides/` | One file per slide, with its speaker notes at the top |
| `assets/deck.css` | Fonts, reset and slide player styles |
| `assets/deck.js` | Slide player (navigation, builds, transitions), as exported |
| `assets/motion.json` | Builds and transitions of each slide |
| `assets/loader.js` | Loads the slides into `index.html`, then starts the player |
| `split_deck.py`, `loader.template.js` | The tool that produces all of the above from an export |
