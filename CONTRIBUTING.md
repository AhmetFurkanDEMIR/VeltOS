# Contributing to VeltOS

Thanks for helping. VeltOS is built in small, verified steps; please keep
changes focused and backed by evidence.

1. Read [AGENTS.md](AGENTS.md) — the project rules apply to humans too.
2. Check [docs/status.md](docs/status.md) for what is done and what is next.
3. Build and test locally (`build/run.sh packages`, `build/run.sh iso`,
   `build/run.sh test`); see [docs/build-guide.md](docs/build-guide.md).
4. Include in your pull request: what changed, why, how you tested it, and
   the actual results (screenshots/report excerpts for image changes).
5. Update the docs you touched: README of the component, `docs/status.md`,
   `docs/development-log.md`, and `docs/architecture.md` for design changes.

Style: English everywhere, LF line endings, `bash` scripts with
`set -euo pipefail`, Debian packaging with debhelper compat 13.

Licensing: code contributions are GPL-3.0-or-later; artwork contributions
are CC-BY-SA-4.0. Only contribute work you have the right to license.
