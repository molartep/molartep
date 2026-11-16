# Profile maintenance

`README.md` provides accessible text and clickable project links below a theme-aware terminal card. The card generator uses Python's standard library and Git. Pillow is only needed to recreate the portrait.

## Update content or statistics

Edit profile labels and featured projects in `scripts/build_profile.py`, and keep their descriptions in `README.md` in sync. Run `python3 scripts/build_profile.py` to rebuild both cards from the saved public stats. Use `--refresh` to fetch current public data; optionally set `GITHUB_TOKEN` for authenticated API limits.

The workflow runs daily at 11:23 UTC (06:23 in Colombia), manually, or after generator/portrait changes on `main`. It commits only the snapshot and generated cards. GitHub must allow Actions with repository content write access. Scheduled workflows become active after these files reach the default branch; GitHub can delay scheduled jobs or disable schedules on inactive public repositories.

Repos includes all owned public repositories. Commits and line totals cover only owned public non-fork repositories, on each default branch. GitHub's author filter resolves identities linked to the account. Commit SHAs are deduplicated across repositories. Full histories are cloned temporarily to read exact `git log --numstat --no-renames --no-merges` text diffs for those commits. Merge commits count toward Commits but contribute no line changes; binary diffs are excluded. Renames are treated as additions/deletions. These are cumulative history statistics, including non-code text, not a current source-only inventory. Net lines always equals added minus deleted.

Repository and commit API pagination is supported. `GITHUB_TOKEN` is recommended for refreshing stats across multiple repositories (the workflow supplies its built-in token). Any fetch or clone failure stops the build before replacing the previous stats and cards. Public histories are cloned without credentials and temporary clones are removed after each repository. The workflow token only writes the generated snapshot/cards in this repository.

## Recreate the portrait

The original JPEG is not committed. `assets/portrait.txt` contains the actual ASCII characters; `assets/portrait.json` contains original sampled colors, crop dimensions, and a source-file SHA-256 hash. The renderer uses these to produce escaped SVG text, without embedding a photograph or loading external images/fonts.

To regenerate from the attached original:

```sh
python3 -m venv /tmp/profile-portrait-venv
/tmp/profile-portrait-venv/bin/pip install Pillow
/tmp/profile-portrait-venv/bin/python scripts/convert_portrait.py /path/to/Headshot.jpeg
python3 scripts/build_profile.py
```

The crop and backdrop silhouette in `convert_portrait.py` are deliberately specific to this supplied photo. Adjust them if using a different portrait. Pillow is needed only for this conversion, not for daily statistics or SVG rendering.

## Validate

```sh
python3 -m unittest discover -s tests
python3 scripts/build_profile.py
git diff --check
```

Preview both SVGs after changing the layout. SVG text uses local monospace fallbacks; character positions in the portrait are explicit to retain alignment across systems. The Markdown content below the card remains readable on narrow screens and by assistive technology.

## Image cache refresh

Each build assigns both README image URLs a SHA-256 version derived from the corresponding generated SVG. A changed card gets a new URL; unchanged cards keep their URL. The stats workflow commits README.md together with the generated SVGs so the profile requests updated images.
