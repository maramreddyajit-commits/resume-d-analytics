# Public release

Repository: https://github.com/maramreddyajit-commits/resume-d-analytics

Public demo: https://maramreddyajit-commits.github.io/resume-d-analytics/

Sections: #churniq, #experimentlab, #marketscope, #demandcast.

GitHub Pages deploys the main branch /docs directory. The repository and public demo are separate from Resume S and the existing personal portfolio; those were not changed. The analytics source, SQL, tests, provenance, case studies, learning guides and aggregate results are public. Raw customer IDs/workbooks, local processed databases and private résumé files are excluded by .gitignore.

All four browser smoke scripts were executed against the public URL in fresh unauthenticated browser contexts after GitHub Pages reported built. Project controls, downloads and mobile checks passed; evidence/*-browser.json and screenshots are from the published views. The public site serves precomputed analytics plus client-side filtering/scenarios. It does not run Python, perform live model training or ingest public user data.

To publish changes: run analysis/tests, commit docs and source together, then push main. To reproduce hosting elsewhere, serve docs/ as static files with relative assets. No paid hosting plan or new API credentials were required.

The updated Resume D includes six clickable project destinations (three demos and three project-source folders). Its private PDF/source/metric ledger are in resume/ locally and excluded from Git.
