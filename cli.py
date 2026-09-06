#!/usr/bin/env python3
"""ManifestPilot CLI.

Scan a project's dependency-tree fixture and PrivacyInfo.xcprivacy for
missing required-reason API declarations and required SDK signatures, or
generate the fixed manifest plus a diff and PR description.
"""
import argparse
import os
import sys

import manifest
import report
import scanner


def cmd_scan(args):
    manifest_path = os.path.join(args.project, "PrivacyInfo.xcprivacy")
    m = manifest.read_manifest(manifest_path)
    findings, notices = scanner.scan(args.project, m)

    print(report.render_scan_report(findings, notices))
    return 1 if findings else 0


def cmd_fix(args):
    manifest_path = os.path.join(args.project, "PrivacyInfo.xcprivacy")
    m = manifest.read_manifest(manifest_path)
    findings, notices = scanner.scan(args.project, m)

    original_bytes = manifest.manifest_bytes(m)
    fixed = manifest.apply_fixes(m, scanner.fixes_for(findings))
    fixed_bytes = manifest.manifest_bytes(fixed)

    os.makedirs(args.out, exist_ok=True)

    with open(os.path.join(args.out, "PrivacyInfo.xcprivacy"), "wb") as f:
        f.write(fixed_bytes)

    diff_text = report.render_diff(original_bytes, fixed_bytes)
    with open(os.path.join(args.out, "PrivacyInfo.xcprivacy.diff"), "w") as f:
        f.write(diff_text)

    pr_description = report.render_pr_description(findings, notices, diff_text)
    with open(os.path.join(args.out, "PR_DESCRIPTION.md"), "w") as f:
        f.write(pr_description)

    print(f"Wrote fixed manifest, diff, and PR description to {args.out}")
    print()
    print(report.render_scan_report(findings, notices))
    return 0


def main():
    parser = argparse.ArgumentParser(prog="cli.py", description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_parser = subparsers.add_parser("scan", help="scan a project for compliance findings")
    scan_parser.add_argument("--project", required=True, help="path to project fixture directory")
    scan_parser.set_defaults(func=cmd_scan)

    fix_parser = subparsers.add_parser("fix", help="write a fixed manifest, diff, and PR description")
    fix_parser.add_argument("--project", required=True, help="path to project fixture directory")
    fix_parser.add_argument("--out", required=True, help="output directory")
    fix_parser.set_defaults(func=cmd_fix)

    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
