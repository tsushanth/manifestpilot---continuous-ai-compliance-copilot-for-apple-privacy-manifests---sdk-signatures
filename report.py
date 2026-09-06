"""Render scan findings, a unified diff, and a markdown PR description."""
import difflib


def render_scan_report(findings, notices):
    lines = ["Privacy Manifest Findings (blocking):"]
    if not findings:
        lines.append("  (none)")
    else:
        for f in findings:
            lines.append(f"  - {f.message}")

    lines.append("")
    lines.append("SDK Signature Notices (informational):")
    if not notices:
        lines.append("  (none)")
    else:
        for n in notices:
            lines.append(f"  - {n.message}")

    return "\n".join(lines)


def render_diff(original_bytes, fixed_bytes, filename="PrivacyInfo.xcprivacy"):
    original_lines = original_bytes.decode("utf-8").splitlines(keepends=True)
    fixed_lines = fixed_bytes.decode("utf-8").splitlines(keepends=True)
    diff = difflib.unified_diff(
        original_lines,
        fixed_lines,
        fromfile=f"a/{filename}",
        tofile=f"b/{filename}",
    )
    return "".join(diff)


def render_pr_description(findings, notices, diff_text):
    lines = ["# ManifestPilot: update PrivacyInfo.xcprivacy", ""]

    if findings:
        lines.append("## Missing required-reason API declarations")
        lines.append("")
        lines.append(
            "The following third-party SDKs access required-reason APIs that "
            "are not (fully) declared in `PrivacyInfo.xcprivacy`. This PR adds "
            "the missing categories/reasons to pre-empt an ITMS-91061 rejection."
        )
        lines.append("")
        for f in findings:
            lines.append(f"- {f.message}")
        lines.append("")
    else:
        lines.append("No missing required-reason API declarations were found.")
        lines.append("")

    if notices:
        lines.append("## SDK signature notices (not modified by this PR)")
        lines.append("")
        lines.append(
            "These SDKs are on Apple's list of libraries that must ship a "
            "validated signature. This PR does not touch binaries or "
            "signatures — verify manually before submitting to App Review."
        )
        lines.append("")
        for n in notices:
            lines.append(f"- {n.message}")
        lines.append("")

    lines.append("## Diff")
    lines.append("")
    lines.append("```diff")
    lines.append(diff_text.rstrip("\n"))
    lines.append("```")
    return "\n".join(lines) + "\n"
