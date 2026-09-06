import os

import manifest
import scanner

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures", "sample-app")


def _load():
    sdk_rules, api_rules = scanner.load_rules()
    m = manifest.read_manifest(os.path.join(FIXTURE_DIR, "PrivacyInfo.xcprivacy"))
    return m, sdk_rules, api_rules


def test_scan_finds_missing_categories_and_signature_notice():
    m, sdk_rules, api_rules = _load()

    findings, notices = scanner.scan(FIXTURE_DIR, m, sdk_rules, api_rules)

    found = {(f.sdk_key, f.category, f.reason) for f in findings}
    assert found == {
        ("app-lovin-sdk", "NSPrivacyAccessedAPICategoryUserDefaults", "CA92.1"),
        ("app-lovin-sdk", "NSPrivacyAccessedAPICategorySystemBootTime", "35F9.1"),
        ("appsflyerframework", "NSPrivacyAccessedAPICategoryUserDefaults", "AC6B.1"),
        ("adjust-ios-sdk", "NSPrivacyAccessedAPICategoryUserDefaults", "1C8F.1"),
    }
    # AppsFlyer's FileTimestamp requirement is already declared in the fixture.
    assert not any(f.category == "NSPrivacyAccessedAPICategoryFileTimestamp" for f in findings)

    assert {n.sdk_key for n in notices} == {"sdwebimage"}


def test_scan_on_fully_compliant_manifest_yields_zero_blocking_findings():
    m, sdk_rules, api_rules = _load()

    findings, _ = scanner.scan(FIXTURE_DIR, m, sdk_rules, api_rules)
    fixed = manifest.apply_fixes(m, scanner.fixes_for(findings))

    findings_after, notices_after = scanner.scan(FIXTURE_DIR, fixed, sdk_rules, api_rules)

    assert findings_after == []
    # Signature notices are informational and independent of manifest fixes.
    assert {n.sdk_key for n in notices_after} == {"sdwebimage"}
