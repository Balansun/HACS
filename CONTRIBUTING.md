# Contributing to Balansun HACS

Thank you for helping improve the Balansun Home Assistant integration.

## Development setup

1. Clone this repository and use a feature branch (or `main` after merge).
2. Install dev dependencies: `pip install -r requirements-dev.txt`
3. Run unit tests: `./scripts/test-unit.sh`
4. Run hardware contract tests only when you have a lab router (never commit tokens):

```bash
export BALANSUN_FIELD_URL=http://192.168.2.159
export BALANSUN_API_BEARER_TOKEN=<your PAT>
pytest -m hardware -q
```

## Pull requests

- One logical change per PR when possible (store hygiene vs entity parity).
- CI must pass: brand gate, HACS validation, hassfest, `compileall`, `pytest -m "not hardware"`.
- Do not include router passwords, API tokens, or LAN IPs in issues or PR descriptions.

## Release checklist (maintainers)

**Nightly (automatic):** merges to `main` that touch integration paths publish `vX.Y.Z-nightly.<sha>` pre-releases when CI is green. No maintainer tagging required — update `CHANGELOG.md` under `[Unreleased]` and bump `manifest.json` `version` when the embedded base semver changes.

0. On GitHub (**TheGrimmChester** account → repo **Settings → General**):
   - **Description:** `Home Assistant custom integration for Balansun ESP32 PV excess routers (REST companion to MQTT discovery).`
   - **Topics:** `homeassistant`, `hacs`, `integration`
   HACS validation in CI must pass with no `ignore` entries (required before HACS default store submission).

## Commits

Follow the repository’s existing message style. Integration code is **EUPL-1.2** (see `LICENSE`).
