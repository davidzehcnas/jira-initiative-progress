# Jira Initiative Progress

Small Python utility that pulls an initiative from Jira and prints the same markdown table format used above, including the green progress bar based on done tasks.

## Usage

Set your credentials and pass the initiative key:

```bash
export JIRA_EMAIL="your.name@glovoapp.com"
export JIRA_API_TOKEN="your-token-here"
python3 initiative_progress.py PROJ-123
```

The initiative key is the Jira issue key of the top-level initiative (e.g. `PROJ-123`). The script fetches all epics under it, counts the child tasks per status, and prints a markdown progress table to stdout.

## Requirements

- Python 3.9+
- Jira Cloud access
- A personal Atlassian API token

## Authentication

This script authenticates exclusively with a **personal Atlassian API token**. Even if you log in to Jira with your Google work account, scripts cannot reuse that browser session — they need an API token.

### Create your token

Go to: `https://id.atlassian.com/manage-profile/security/api-tokens`

Click **Create API token**, give it a label (e.g. `jira-utils`), and copy the value immediately — it is only shown once.

### Verify your setup

Before running a real query you can confirm that the credentials and site are correct with `--check`:

```bash
export JIRA_EMAIL="your.name@glovoapp.com"
export JIRA_API_TOKEN="your-token-here"
python3 initiative_progress.py --check
```

Expected output on success:

```
Connection successful.
  User:  David Sanchez
  Email: your.name@glovoapp.com
  Site:  glovoapp.atlassian.net
```

If the token is wrong or revoked the script exits with a non-zero code and prints the HTTP error returned by Jira (usually `401 Unauthorized`).

### Provide credentials at runtime

Pass the credentials via environment variables:

```bash
export JIRA_EMAIL="your.name@glovoapp.com"
export JIRA_API_TOKEN="your-token-here"
python3 initiative_progress.py PROJ-123
```

`JIRA_SITE` defaults to `glovoapp.atlassian.net`. Override it only if needed:

```bash
export JIRA_SITE="other-org.atlassian.net"
```

### Storing credentials securely (never commit them)

The token must **never** appear in any file tracked by git. The options below go from simplest to most secure:

**Option A — Shell profile (simplest)**

Add the exports to `~/.zshrc` (or `~/.zprofile` for login shells):

```bash
# ~/.zshrc  — keep this file out of any git repo
export JIRA_EMAIL="your.name@glovoapp.com"
export JIRA_API_TOKEN="your-token-here"
```

Reload with `source ~/.zshrc`. The token lives only on your machine in a file that is never inside a git working tree.

**Option B — `direnv` + `.env` file (recommended for per-project isolation)**

1. Install `direnv` (`brew install direnv`) and hook it into your shell.
2. Create a `.env` file **inside the project directory**:

   ```bash
   # .env  — never committed
   export JIRA_EMAIL="your.name@glovoapp.com"
   export JIRA_API_TOKEN="your-token-here"
   ```

3. Allow the directory: `direnv allow .`
4. Make absolutely sure `.env` is gitignored:

   ```bash
   echo '.env' >> .gitignore
   ```

`direnv` loads the variables automatically when you `cd` into the directory and unloads them when you leave.

**Option C — macOS Keychain (most secure)**

Store the token in the system keychain so it is encrypted at rest and never written to any plain-text file:

```bash
# Store once
security add-generic-password -a "$USER" -s jira-api-token -w "your-token-here"

# Retrieve in your shell profile or a wrapper script
export JIRA_API_TOKEN="$(security find-generic-password -a "$USER" -s jira-api-token -w)"
```

The `security` command is built into macOS — no extra tools needed.

### .gitignore checklist

If this project ever gets a git remote, make sure the following are always gitignored:

```
.env
*.env
.envrc
```

Never rely on git to keep a secret safe after it has been committed even once — it will remain in the history. If a token is accidentally committed, **rotate it immediately** on `https://id.atlassian.com/manage-profile/security/api-tokens`.

## Output

The script prints markdown like this:

```md
| Epic | Progress | ⬜ Not started | 🟧 In progress | 🟪 In review | 🟩 Done |
|---|---|---:|---:|---:|---:|
| Pagination in clients | 🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩 100.0% (14) | 0.0% (0) | 0.0% (0) | 0.0% (0) | 100.0% (14) |
```

## Notes

- Epic order is preserved from the initiative order in Jira.
- The progress bar only reflects the done percentage.
- The final row aggregates all child tasks from all epics.
- Child task lookup first tries `parentEpic`, then falls back to `Epic Link` for older Jira setups.

## Flags

### `--check`

Tests whether the credentials and site are reachable without running any real query. Use this the first time you set up the script, or whenever you rotate your API token.

```bash
python3 initiative_progress.py --check
```

No initiative key is needed. The script exits with code 0 on success and prints the authenticated user's name, email, and site. It exits with a non-zero code and prints the Jira error on failure.

---

### `--site`

The Jira Cloud hostname to connect to. Defaults to `glovoapp.atlassian.net`, which is correct for most uses. Only set this if you need to point the script at a different Atlassian organisation.

```bash
python3 initiative_progress.py PROJ-123 --site other-org.atlassian.net
```

Can also be set via the `JIRA_SITE` environment variable.

---

### `--email`

Your Atlassian account email address. This is the email you use to log in to Jira, even if you normally authenticate via Google SSO.

```bash
python3 initiative_progress.py PROJ-123 --email your.name@glovoapp.com
```

Prefer setting this via the `JIRA_EMAIL` environment variable so it is not visible in your shell history.

---

### `--api-token`

Your personal Atlassian API token. Create one at `https://id.atlassian.com/manage-profile/security/api-tokens`.

```bash
python3 initiative_progress.py PROJ-123 --api-token your-token-here
```

Prefer setting this via the `JIRA_API_TOKEN` environment variable so it is not visible in your shell history.

---

### `--blocks`

Controls how wide the progress bar is, measured in emoji blocks. Each block represents an equal slice of the total. Defaults to `10`. Increase it for more granularity, decrease it for a more compact output.

```bash
python3 initiative_progress.py PROJ-123 --blocks 20
```

A value of `20` means each block represents 5% of progress. A value of `4` means each block represents 25%.

---

### `--no-total`

By default the table includes a final **Total** row that aggregates the counts of every epic. Pass this flag to omit that row, for example when pasting the table somewhere that already has its own summary.

```bash
python3 initiative_progress.py PROJ-123 --no-total
```

---

### `--ignore-epics`

Excludes one or more epics from the table and from all totals. Pass the Jira issue keys of the epics you want to skip, space-separated. Useful for epics that are on hold, out of scope, or belong to a different team but still appear under the initiative in Jira.

```bash
python3 initiative_progress.py PROJ-123 --ignore-epics PROJ-456 PROJ-789
```

The keys are case-insensitive. The script prints a confirmation line to stderr listing which epics were ignored before fetching their children, so no unnecessary API calls are made for them.

---

### `--timeout`

How many seconds to wait for a response from the Jira API before giving up. Defaults to `30`. Raise it if you are on a slow connection or querying a very large initiative.

```bash
python3 initiative_progress.py PROJ-123 --timeout 60
```
