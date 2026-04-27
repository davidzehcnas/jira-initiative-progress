from __future__ import annotations

import argparse
import os
from dataclasses import dataclass


DEFAULT_SITE = "your-org.atlassian.net"
DEFAULT_BLOCKS = 10


@dataclass
class JiraConfig:
    email: str
    api_token: str
    site: str
    timeout: int

    @property
    def base_url(self) -> str:
        return f"https://{self.site}/rest/api/3"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the initiative progress markdown table from Jira.",
    )
    parser.add_argument(
        "initiative_key",
        nargs="?",
        help="Initiative issue key, for example PROJ-123. Not required when using --check.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify that credentials and site are valid, then exit. No initiative key needed.",
    )
    parser.add_argument(
        "--site",
        default=os.environ.get("JIRA_SITE", DEFAULT_SITE),
        help=f"Jira site hostname. Default: {DEFAULT_SITE}",
    )
    parser.add_argument(
        "--email",
        default=os.environ.get("JIRA_EMAIL"),
        help="Atlassian account email. Can also be set via JIRA_EMAIL.",
    )
    parser.add_argument(
        "--api-token",
        default=os.environ.get("JIRA_API_TOKEN"),
        help="Personal Atlassian API token. Can also be set via JIRA_API_TOKEN.",
    )
    parser.add_argument(
        "--blocks",
        type=int,
        default=DEFAULT_BLOCKS,
        help=f"Progress bar size. Default: {DEFAULT_BLOCKS}",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="HTTP timeout in seconds. Default: 30",
    )
    parser.add_argument(
        "--no-total",
        action="store_true",
        help="Skip the final aggregated row.",
    )
    parser.add_argument(
        "--ignore-epics",
        nargs="+",
        default=[],
        metavar="KEY",
        help="Epic keys to exclude from the table and totals, e.g. PROJ-456 PROJ-789.",
    )
    return parser.parse_args()


def resolve_config(args: argparse.Namespace) -> JiraConfig:
    email = args.email
    api_token = args.api_token

    if not email or not api_token:
        raise SystemExit(
            "Missing Jira credentials. Set JIRA_EMAIL and JIRA_API_TOKEN environment variables.\n\n"
            "Create a personal API token at: https://id.atlassian.com/manage-profile/security/api-tokens\n"
            "Use your Atlassian account email as the username, even when logging in via Google SSO."
        )

    return JiraConfig(
        email=email,
        api_token=api_token,
        site=args.site,
        timeout=args.timeout,
    )
