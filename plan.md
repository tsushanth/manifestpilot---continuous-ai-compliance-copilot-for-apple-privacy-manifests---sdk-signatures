# ManifestPilot — Local MVP Scaffold Plan

## Goal of this MVP

Prove the core value loop end-to-end, entirely offline, on fixture data:

> given an app's dependency tree + its current `PrivacyInfo.xcprivacy`, detect
> which third-party SDKs/APIs are out of compliance with Apple's
> privacy-manifest and required-reason-API rules, and auto-generate the fixed
> manifest plus a human-readable "PR" (diff + description) that a real CI job
> would open against the repo.

Everything about *continuously* tracking Apple's policy changes, running in
real CI, and actually opening GitHub PRs is the eventual product — not this
scaffold. The scaffold just has to prove the analysis + auto-fix engine works
on a realistic input.

## 1. Stack

**Plain Python 3 CLI, standard library only, no framework.**

Why Python over Node/Go for this specific demo:
- `.xcprivacy` files are Apple property lists (XML plist). Python's stdlib
  `plistlib` reads/writes/merges them natively with zero dependencies. Node
  would need a third-party plist package; Go would need to hand-roll XML
  plist parsing.
- Dependency-tree fixtures (`Podfile.lock` YAML-ish, or Swift Package
  `Package.resolved` JSON) are trivial to parse with stdlib `json`/simple
  text parsing — no need for a real CocoaPods/SwiftPM implementation.
- A CLI with `argparse` subcommands (`scan`, `fix`) is enough; no server, no
  build step, no package manager beyond what ships with Python 3.
- `pytest` for tests (only third-party dependency, dev-only).

No web framework, no database, no queue, no LLM call is required for the
MVP — this is deterministic rule-matching + file merging, which is the
actual mechanism of value (an LLM could later help draft PR prose, but that's
not what proves the idea).

## 2. Explicitly out of scope for this local MVP

- **No real GitHub integration.** "Auto-opens pull requests" is demoed as:
  write the fixed `PrivacyInfo.xcprivacy` to disk + emit a unified diff +
  emit a markdown PR description file. No GitHub API calls, no tokens, no
  git commit/push.
- **No CI integration.** No GitHub Actions workflow, no webhook listener, no
  "runs on every dependency bump" scheduler. The CLI is invoked manually.
- **No live tracking of Apple's policy pages.** The required-reason API list
  and the SDK-signature list ship as static local JSON snapshots (hand-seeded
  from the public docs already gathered). "Continuously tracks Apple's
  evolving rules" becomes future work (a scraper/updater job) — out of scope
  here.
- **No real binary/Mach-O scanning** (no `otool`/`nm`/symbol analysis of an
  actual `.ipa`). SDK presence is inferred from a dependency-lockfile fixture
  instead of a compiled binary — sufficient to prove the matching/fix logic.
- **No auth, no accounts, no billing, no hosting/deploy.** Pure local CLI.
- **No multi-project/config management UI.** One fixture app, one run.

None of these are needed to demonstrate the core value (detect drift →
generate correct fix); they're all delivery/integration concerns for a later
milestone.

## 3. File / directory layout

```
manifestpilot/
├── cli.py                        # argparse entry point: `scan` and `fix` subcommands
├── scanner.py                    # parses dependency fixture, matches SDKs/APIs against rules
├── manifest.py                   # reads/merges/writes PrivacyInfo.xcprivacy (plistlib)
├── report.py                     # renders scan findings + diff + PR-description markdown
├── rules/
│   ├── sdk_signatures.json       # known third-party SDKs -> {requires_signature, requires_manifest}
│   └── required_reason_apis.json # API category -> allowed NSPrivacyAccessedAPITypeReasons
├── fixtures/
│   └── sample-app/
│       ├── Package.resolved.json # stand-in dependency tree (a few known SDKs, one non-compliant)
│       └── PrivacyInfo.xcprivacy # intentionally incomplete, to be fixed by the tool
├── tests/
│   ├── test_scanner.py           # rule-matching logic against fixture data
│   └── test_manifest.py          # plist merge logic (idempotency, no data loss on merge)
└── plan.md                       # this file
```

## 4. Verification

- **Unit tests (`pytest`)**:
  - `test_scanner.py`: given the sample dependency tree, asserts the correct
    set of "missing manifest entry" and "missing signature" findings is
    produced, and that a fully-compliant fixture yields zero findings.
  - `test_manifest.py`: asserts merging a fix into an existing
    `PrivacyInfo.xcprivacy` preserves unrelated existing entries, is
    idempotent (running fix twice produces the same output), and produces
    valid plist XML.
- **Manual run-through**:
  1. `python cli.py scan --project fixtures/sample-app` → prints findings
     (e.g. "SDK `AppLovinSDK` requires a privacy manifest entry for
     `NSPrivacyAccessedAPICategoryUserDefaults`, none found").
  2. `python cli.py fix --project fixtures/sample-app --out /tmp/out` →
     writes the corrected `PrivacyInfo.xcprivacy`, a `.diff` file, and a
     `PR_DESCRIPTION.md`.
  3. Manually diff `/tmp/out/PrivacyInfo.xcprivacy` against the fixture's
     original to confirm only the expected entries were added, nothing else
     changed.
  4. Re-run `scan` against the fixed output and confirm zero findings —
     proves the loop actually closes.
