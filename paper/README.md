# Research papers: public display adaptations

The English and Chinese PDFs adapt the latest reviewed plain-language papers in the author's original final-deliverables directory, whose hashes are recorded in `adaptation_manifest.json` and `results/frozen_summary.json`. They retain the 20,000 / 10,117 / 3,562 / 3,285 / 82 flow and the complete 40-layer conclusions. They are clearly marked on page one and in each footer.

The adaptations withhold Section 5.3's candidate expressions, Alpha IDs and individual platform metrics; remove the individual correlation value and submission record detail; replace the opening expression example with a declared teaching expression; and point the supplement reference to released methods/aggregates. Figure 2 displays six-band yield and per-layer counts, replacing the private candidate-order cumulative plot. The conclusions have not been re-estimated.

The original unredacted PDFs, original supplement, workbooks and records remain untouched in the private archive. The label “public display adaptation” describes the content reduction; Public visibility still requires the author's final rights review and approval.

Editable Markdown sources are included. To rebuild, install the paper extra and run `python scripts/build_papers.py`. The renderer expects Times New Roman, Arial, Arial Unicode and Courier New TTF fonts, using standard macOS font locations or the `ALPHA_PAPER_FONT_DIR` environment variable. Fonts are not redistributed. On other operating systems supply legally obtained equivalent named fonts or adapt the font mapping, and render/inspect all pages after a typography change. Rebuilding is optional for the synthetic demo.
