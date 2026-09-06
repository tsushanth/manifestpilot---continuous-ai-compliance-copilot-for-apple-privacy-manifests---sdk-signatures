"""Match a dependency-tree fixture against the SDK-signature and
required-reason-API rule snapshots, and report:

- ManifestFinding: a third-party SDK accesses a required-reason API
  category/reason that is not declared in PrivacyInfo.xcprivacy. These are
  "blocking" and auto-fixable (manifest.apply_fixes resolves them).
- SignatureNotice: a third-party SDK is on Apple's list of libraries that
  must ship a valid signature. These are informational only — no local file
  edit can fix a binary signature, so `fix` reports but does not act on them.
"""
import json
import os
from dataclasses import dataclass

from manifest import ACCESSED_API_TYPES_KEY, API_TYPE_KEY, API_TYPE_REASONS_KEY

RULES_DIR = os.path.join(os.path.dirname(__file__), "rules")


@dataclass
class ManifestFinding:
    sdk_key: str
    sdk_display_name: str
    category: str
    reason: str
    reason_description: str

    @property
    def message(self):
        return (
            f"SDK '{self.sdk_display_name}' accesses {self.category} "
            f"(reason {self.reason}: {self.reason_description}) — not declared "
            f"in PrivacyInfo.xcprivacy"
        )


@dataclass
class SignatureNotice:
    sdk_key: str
    sdk_display_name: str
    note: str

    @property
    def message(self):
        return f"SDK '{self.sdk_display_name}' requires a validated signature: {self.note}"


def load_rules(rules_dir=RULES_DIR):
    with open(os.path.join(rules_dir, "sdk_signatures.json")) as f:
        sdk_rules = json.load(f)
    with open(os.path.join(rules_dir, "required_reason_apis.json")) as f:
        api_rules = json.load(f)
    return sdk_rules, api_rules


def load_dependencies(project_dir):
    path = os.path.join(project_dir, "Package.resolved.json")
    with open(path) as f:
        data = json.load(f)
    return [pin["identity"].lower() for pin in data.get("pins", [])]


def _existing_reasons(manifest):
    return {
        entry[API_TYPE_KEY]: set(entry.get(API_TYPE_REASONS_KEY, []))
        for entry in manifest.get(ACCESSED_API_TYPES_KEY, [])
    }


def scan(project_dir, manifest, sdk_rules=None, api_rules=None):
    if sdk_rules is None or api_rules is None:
        sdk_rules, api_rules = load_rules()

    identities = load_dependencies(project_dir)
    existing = _existing_reasons(manifest)

    findings = []
    notices = []

    for identity in identities:
        rule = sdk_rules.get(identity)
        if rule is None:
            continue
        display_name = rule.get("display_name", identity)

        if rule.get("requires_privacy_manifest"):
            for req in rule.get("api_categories", []):
                category, reason = req["category"], req["reason"]
                if reason in existing.get(category, set()):
                    continue
                reason_description = api_rules.get(category, {}).get("allowed_reasons", {}).get(reason, "")
                findings.append(
                    ManifestFinding(identity, display_name, category, reason, reason_description)
                )

        if rule.get("requires_signature"):
            notices.append(SignatureNotice(identity, display_name, rule.get("signature_note", "")))

    return findings, notices


def fixes_for(findings):
    """Group manifest findings into {category: {reason, ...}} for manifest.apply_fixes."""
    grouped = {}
    for f in findings:
        grouped.setdefault(f.category, set()).add(f.reason)
    return grouped
