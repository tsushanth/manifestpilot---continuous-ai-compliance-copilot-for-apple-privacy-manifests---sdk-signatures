"""Read, merge, and write PrivacyInfo.xcprivacy plist files."""
import plistlib
from copy import deepcopy

ACCESSED_API_TYPES_KEY = "NSPrivacyAccessedAPITypes"
API_TYPE_KEY = "NSPrivacyAccessedAPIType"
API_TYPE_REASONS_KEY = "NSPrivacyAccessedAPITypeReasons"


def read_manifest(path):
    with open(path, "rb") as f:
        return plistlib.load(f)


def manifest_bytes(data):
    return plistlib.dumps(data, fmt=plistlib.FMT_XML, sort_keys=True)


def write_manifest(path, data):
    with open(path, "wb") as f:
        f.write(manifest_bytes(data))


def apply_fixes(manifest, category_reasons):
    """Return a new manifest with the given {category: {reason, ...}}
    additions merged in. Existing entries and unrelated keys are preserved
    untouched. Idempotent: applying the same fixes twice yields the same
    result, since already-declared reasons are skipped.
    """
    fixed = deepcopy(manifest)
    entries = fixed.setdefault(ACCESSED_API_TYPES_KEY, [])
    by_category = {entry[API_TYPE_KEY]: entry for entry in entries}

    for category, reasons in category_reasons.items():
        entry = by_category.get(category)
        if entry is None:
            entry = {API_TYPE_KEY: category, API_TYPE_REASONS_KEY: []}
            entries.append(entry)
            by_category[category] = entry
        existing_reasons = entry.setdefault(API_TYPE_REASONS_KEY, [])
        for reason in sorted(reasons):
            if reason not in existing_reasons:
                existing_reasons.append(reason)

    return fixed
