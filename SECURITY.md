# Security and private data

Atelier is an early-development application for a trusted private workspace.
It does not currently implement application authentication, user roles, or
per-user access to records and connected services.

## Deployment boundary

Native startup and Docker's host port mapping default to localhost. Keep that
boundary unless you supply and verify an authenticated access layer. Anyone who
can reach an unprotected instance may access or change its catalogue and outreach
records and use a connected Gmail account. Gmail authorization authenticates the
server to Google; it does not authenticate visitors to Atelier.

Do not publish the application port directly to the internet. Imported records
and remote image URLs are also untrusted input: input handling and rendering
need further hardening before public or multi-user deployment. Local binding
reduces network exposure but is not a substitute for those controls.

## Keep private material out of source control

- Store credentials, OAuth tokens, private research, collection data and backups
  in ignored local locations. Treat the complete `data/` directory as private.
- Never attach `.env`, databases, Gmail tokens, message bodies, contact lists,
  authenticated screenshots, machine addresses, or private filesystem paths.
- Screenshots need a visual review as well as metadata removal. Use sample data
  for contact, mail, and account pages.
- Run `python scripts/check_publication.py` before a contribution. A separate
  secret scanner such as Gitleaks complements this targeted check; neither proves
  that all personal information has been found.

An ignore rule does not remove files that Git already tracks. Deleting a tracked
file also does not remove it from existing commits, clones, or caches. If a real
credential is exposed, revoke it first; history cleanup is a separate operation
that must be coordinated with repository maintainers.

## Reporting

Use GitHub's private vulnerability reporting option if it is enabled. Otherwise
ask the maintainer for a private reporting channel without including credentials,
private records, or exploit details in a public issue.
