# Contributing to VeltOS

Thanks for helping. VeltOS is built in small, verified steps; please keep
changes focused and backed by evidence.

1. Read [AGENTS.md](AGENTS.md) — the project rules apply to humans too.
2. Check [docs/dev/status.md](docs/dev/status.md) for what is done and what
   is next.
3. Build and test locally (`build/run.sh packages`, `build/run.sh iso`,
   `build/run.sh test`); see [docs/dev/build-guide.md](docs/dev/build-guide.md).
4. Include in your pull request: what changed, why, how you tested it, and
   the actual results (screenshots or report excerpts for image changes).
5. Update the docs you touched: the component's README,
   `docs/dev/status.md`, `docs/dev/development-log.md`, and
   `docs/dev/architecture.md` for design changes.

The website lives in `docs/` (static HTML, CSS and JavaScript, published by
GitHub Pages); every text needs its English and Turkish version, and every
claim on it the same evidence as the rest of the project. See "The website"
in AGENTS.md.

Report bugs and ideas on
[GitHub Issues](https://github.com/AhmetFurkanDEMIR/VeltOS/issues).

Style: English everywhere, LF line endings, `bash` scripts with
`set -euo pipefail`, Debian packaging with debhelper compat 13.

Licensing: code contributions are GPL-3.0-or-later; artwork contributions
are CC-BY-SA-4.0. Only contribute work you have the right to license.
