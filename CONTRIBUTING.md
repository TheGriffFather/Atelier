# Contributing to Atelier

Read the [README](README.md) for the current product and the
[development guide](docs/DEVELOPMENT.md) for setup. The [task index](Tasks/README.md)
contains proposals; check the implementation before assuming a task is complete.

Keep changes focused and explain what changed, why, and how it was checked.
Include screenshots for interface changes, using reviewed sample data. Test
changes with `python -m pytest -q`; rebuild CSS when changing Tailwind classes.

Run `python scripts/check_publication.py` before staging. Add new public files
explicitly, then run it again before committing. Review the staged diff, images,
and any generated assets. The checker examines tracked files and obvious private
artifacts; it cannot determine consent or replace a visual/privacy review.

Never include local research, contact lists, mail contents, account state,
credentials, databases, or original screenshots from a private installation.
See [Security](SECURITY.md) for the current deployment boundary and reporting.

Contributions retain the project's MIT software license. Supply clear provenance
and appropriate permission for artwork or other media; the software license does
not automatically cover those assets.
