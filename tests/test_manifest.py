import copy

import manifest


def _sample():
    return {
        "NSPrivacyTracking": False,
        "NSPrivacyTrackingDomains": [],
        "NSPrivacyCollectedDataTypes": [],
        "NSPrivacyAccessedAPITypes": [
            {
                "NSPrivacyAccessedAPIType": "NSPrivacyAccessedAPICategoryFileTimestamp",
                "NSPrivacyAccessedAPITypeReasons": ["C617.1"],
            }
        ],
    }


def test_apply_fixes_preserves_existing_entries_and_does_not_mutate_input():
    original = _sample()
    baseline = copy.deepcopy(original)

    fixed = manifest.apply_fixes(
        original, {"NSPrivacyAccessedAPICategoryUserDefaults": {"CA92.1", "AC6B.1"}}
    )

    assert original == baseline

    file_ts = next(
        e
        for e in fixed["NSPrivacyAccessedAPITypes"]
        if e["NSPrivacyAccessedAPIType"] == "NSPrivacyAccessedAPICategoryFileTimestamp"
    )
    assert file_ts["NSPrivacyAccessedAPITypeReasons"] == ["C617.1"]

    user_defaults = next(
        e
        for e in fixed["NSPrivacyAccessedAPITypes"]
        if e["NSPrivacyAccessedAPIType"] == "NSPrivacyAccessedAPICategoryUserDefaults"
    )
    assert set(user_defaults["NSPrivacyAccessedAPITypeReasons"]) == {"CA92.1", "AC6B.1"}


def test_apply_fixes_is_idempotent():
    original = {"NSPrivacyAccessedAPITypes": []}
    once = manifest.apply_fixes(original, {"NSPrivacyAccessedAPICategoryUserDefaults": {"CA92.1"}})
    twice = manifest.apply_fixes(once, {"NSPrivacyAccessedAPICategoryUserDefaults": {"CA92.1"}})
    assert once == twice


def test_manifest_bytes_round_trip(tmp_path):
    data = _sample()
    path = tmp_path / "PrivacyInfo.xcprivacy"
    manifest.write_manifest(path, data)
    assert manifest.read_manifest(path) == data
