#!/usr/bin/env python3

from __future__ import annotations

import sys

from jira_utils.client import JiraClient
from jira_utils.config import parse_args, resolve_config
from jira_utils.progress import build_progress, fetch_epics
from jira_utils.renderer import render_markdown_table


def main() -> int:
    args = parse_args()

    config = resolve_config(args)
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
        raise SystemExit("initiative_key is required unless --check is used.")

    print(f"Fetching epics for {args.initiative_key}...", file=sys.stderr)
    epics = fetch_epics(client, args.initiative_key)
    print(f"Found {len(epics)} epic(s). Fetching children...", file=sys.stderr)

    if args.ignore_epics:
        ignore = {k.upper() for k in args.ignore_epics}
        epics = [e for e in epics if e["key"].upper() not in ignore]
        print(f"Ignoring epics: {', '.join(sorted(ignore))}", file=sys.stderr)

    rows = build_progress(epics, client)
    
    print("", file=sys.stderr)
    print(render_markdown_table(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
