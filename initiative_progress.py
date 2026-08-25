#!/usr/bin/env python3

import argparse
import sys

from jira_utils.client import JiraClient
from jira_utils.config import build_config
from jira_utils.progress import build_epics_progress, fetch_epics
from jira_utils.renderer import render_markdown_table

DEFAULT_TIMEOUT = 30


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the initiative progress markdown table from Jira.",
    )
    parser.add_argument(
        "--site",
        help="Jira site hostname. Defaults to JIRA_SITE.",
    )
    parser.add_argument(
        "--initiative-key",
        help="Initiative issue key, for example PROJ-123. Not required when using --check.",
    )
    parser.add_argument("site_positional", nargs="?", help=argparse.SUPPRESS)
    parser.add_argument("initiative_key_positional", nargs="?", help=argparse.SUPPRESS)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify that credentials and site are valid, then exit.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"HTTP timeout in seconds. Default: {DEFAULT_TIMEOUT}",
    )
    parser.add_argument(
        "--ignore-epics",
        nargs="+",
        default=[],
        metavar="KEY",
        help="Epic keys to exclude from the table and totals.",
    )
    parser.add_argument(
        "--add-total",
        action="store_true",
        default=False,
        help="Append a Total row at the bottom of the table.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.site is None:
        args.site = args.site_positional
    if args.initiative_key is None:
        args.initiative_key = args.initiative_key_positional
    config = build_config(args)
    client = JiraClient(config)

    if args.check:
        try:
            user = client.check_connection()
        except RuntimeError as exc:
            raise SystemExit(f"Connection failed: {exc}") from exc
        print("Connection successful.")
        print(f"  User:  {user.get('displayName', '(unknown)')}")
        print(f"  Email: {user.get('emailAddress', '(unknown)')}")
        print(f"  Site:  {config.site}")
        return 0

    if not args.initiative_key:
        raise SystemExit("--initiative-key is required unless --check is used.")

    print(f"Fetching epics under {args.initiative_key}...", file=sys.stderr)
    epics = fetch_epics(client, args.initiative_key)
    print(f"Found {len(epics)} epic(s), now fetching child issues for each...", file=sys.stderr)

    if args.ignore_epics:
        ignore = {k.upper() for k in args.ignore_epics}
        epics = [e for e in epics if e["key"].upper() not in ignore]
        print(f"Skipping {len(ignore)} epic(s): {', '.join(sorted(ignore))}", file=sys.stderr)

    epics_progress = build_epics_progress(epics, client)
    print(render_markdown_table(epics_progress, add_total=args.add_total))

    return 0


if __name__ == "__main__":
    sys.exit(main())
