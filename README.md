# ManifestPilot (local MVP scaffold)

ManifestPilot is a continuous AI compliance copilot for Apple's privacy
manifests: it watches an app's third-party SDK dependency tree, detects
where `PrivacyInfo.xcprivacy` is missing required-reason API declarations
or uses an SDK that now requires a validated signature, and auto-generates
the fix so an ITMS-91061-style rejection never reaches App Review.

This repository is the **local MVP scaffold** described in `plan.md`: a
deterministic, offline CLI that proves the core detect-and-fix loop against
fixture data. It does **not** call GitHub, run in CI, or scan a real
compiled binary — see "Scope" below.

## What it does

1. **`scan`** — reads a project's dependency-tree fixture
   (`Package.resolved.json`) and its `PrivacyInfo.xcprivacy`, matches known
   SDKs against two local rule snapshots (`rules/sdk_signatures.json`,
   `rules/required_reason_apis.json`), and reports:
   - **Privacy Manifest Findings** (blocking) — a required-reason API
     category/reason a matched SDK needs that isn't declared in the
     manifest yet.
   - **SDK Signature Notices** (informational) — a matched SDK is on
     Apple's list of libraries that must ship a validated signature. Since
     this scaffold does no binary/Mach-O scanning, these are flagged but
     never auto-resolved.
2. **`fix`** — recomputes the same findings, merges the missing categories
   and reasons into the existing manifest (preserving everything else,
   idempotently), and writes to an output directory:
   - the corrected `PrivacyInfo.xcprivacy`
   - `PrivacyInfo.xcprivacy.diff` (unified diff against the original)
   - `PR_DESCRIPTION.md` (what a real CI job would put in the PR body)

## Requirements

Python 3.9+, standard library only. `pytest` is the only dependency, and
only for running the test suite.

## Run it

```bash
# 1. Scan the sample fixture app
python3 cli.py scan --project fixtures/sample-app

# 2. Generate the fix
python3 cli.py fix --project fixtures/sample-app --out /tmp/manifestpilot-out

# 3. Inspect what it produced
cat /tmp/manifestpilot-out/PrivacyInfo.xcprivacy.diff
cat /tmp/manifestpilot-out/PR_DESCRIPTION.md

# 4. Confirm the loop closes: re-scanning the fixed manifest in place
#    yields zero blocking findings (the SDK signature notice remains,
#    since fix never touches binaries/signatures)
cp /tmp/manifestpilot-out/PrivacyInfo.xcprivacy fixtures/sample-app/PrivacyInfo.xcprivacy
python3 cli.py scan --project fixtures/sample-app
git checkout -- fixtures/sample-app/PrivacyInfo.xcprivacy  # restore the fixture
```

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

- `tests/test_scanner.py` — rule-matching against the fixture: asserts the
  exact set of missing-manifest-entry findings and signature notices, and
  that fixing them all yields zero blocking findings on re-scan.
- `tests/test_manifest.py` — plist merge logic: preserves unrelated
  entries, doesn't mutate its input, is idempotent, and round-trips through
  valid plist XML.

## Layout

```
cli.py                        # argparse entry point: scan / fix
scanner.py                    # matches dependency fixture against rules
manifest.py                   # reads/merges/writes PrivacyInfo.xcprivacy
report.py                     # renders findings, diff, PR description
rules/
  sdk_signatures.json         # known SDKs -> manifest/signature requirements
  required_reason_apis.json   # API category -> allowed reason codes
fixtures/sample-app/          # a dependency tree + an incomplete manifest
tests/
```

## Scope

This scaffold proves the analysis + auto-fix engine. Explicitly out of
scope here (see `plan.md` for the full rationale):

- No GitHub integration — "opening a PR" is a diff + markdown file on disk.
- No CI integration — the CLI is invoked manually.
- No live tracking of Apple's policy pages — the rule files are static,
  hand-seeded snapshots.
- No real binary/Mach-O scanning — SDK presence comes from a dependency
  lockfile fixture, not a compiled `.ipa`.
