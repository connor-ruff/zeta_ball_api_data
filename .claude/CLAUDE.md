# zeta_ball_api_data — Project Home Base

This repo is the "home base" for the Zeta Ball API data project. The project spans three repos, all under `/Users/connor/source/repos/`. Sessions are started from this repo with the other two added as additional working directories (see `bin/claude-proj-start.sh`).

## Repos in this project

| Repo | Role |
|------|------|
| `zeta_ball_api_data` (this repo) | API-side work: auth and testing scripts (`manual_scripts/`) and analysis SQL (`queries/`). |
| `connors_snowflake_db` | Snowflake object tracker for account `EI90710`. `snowflake_admin/` holds account-level setup (databases, roles, storage integrations). `snowflake_objects/` mirrors the Snowflake object navigator (database > schema > tables/views/procedures). |
| `aws_iac_mngr` | AWS infrastructure for Connor's personal account, managed with OpenTofu (not Terraform). The Lambda source code now lives here. |

## Cross-repo notes

- Each auxiliary repo has its own instructions file. **Before doing any work in one of these repos, read its file first and follow it:**
  - `/Users/connor/source/repos/connors_snowflake_db/.claude/CLAUDE.md`
  - `/Users/connor/source/repos/aws_iac_mngr/.claude/CLAUDE.md`
- Convention: in all repos, `CLAUDE.md` lives inside `.claude/`, not at the repo root.
- Notably, `aws_iac_mngr` requires logging every `aws ...` CLI command and its output to `aws-cli-commands/`.
- AWS profile `connor-ruff-dev-acct`, primary region `us-east-2`. Do not re-run `bootstrap/` in `aws_iac_mngr`.
- Snowflake DDL and objects belong in `connors_snowflake_db`, not in this repo. Lambda and infra changes belong in `aws_iac_mngr`.

## STATUS: PAUSED (as of 2026-10-19) — waiting on Yahoo Fantasy API approval

The 2026-27 season pull is blocked. Nothing is broken in our code; Yahoo is refusing the app.

**What happened**
- Last season's Yahoo refresh token was dead (`invalid_grant`). Re-authorizing worked (token exchange returns 200), but every Fantasy API call returns `403 This application is not authorized to perform this action` (even `game/nba`). A garbage token gets 401, so the token is valid; the *app* isn't authorized for the Fantasy API.
- Same result with the old app and a brand-new app (Fantasy Sports → Read enabled). Cleaning up connected apps and changing the `scope` param made no difference.
- Yahoo now appears to require an application/approval step: https://sports.yahoo.com/developer/application-confirmation/ (sign API Access and Use Agreement; submit name, email, Client ID). **Connor submitted this for the new app on 2026-10-19.** Not confirmed as the cause, but it fits the evidence.

**Current state**
- Secret `yahoo-fantasy--slop-api-keys`: new `app_id`, `client_id`, `client_secret` set. `auth_code`, `refresh_token`, and `zeta_ball_2026_2027_league_key` are intentionally BLANK. `zeta_ball_league_id` is still last season's (6036); verify.
- Secret values are not managed by OpenTofu (container only), so no IaC drift. `tofu plan` in `secrets_manager/` showed no changes.
- Snowflake task `STG.REFRESH_WEEKLY_TASK` is SUSPENDED. Do not resume until the API works. (EventBridge schedule `zeta-ball-api-pull` is an unused relic; leave disabled.)
- `manual_scripts/tester.py` now has `list_my_nba_leagues()`, `get_league_teams()`, `check_league_and_team_keys()` for finding the 2026-27 league key and diffing team keys. A local `manual_scripts/new_secret.json` (gitignored; contains credentials) may exist — delete when done.

**To resume once Yahoo approves**
1. Re-run OAuth: build the auth URL from the secret's `client_id`/`redirect_uri` (scope `fspt-r`), visit it, exchange the `code=` value (expires in minutes). Confirm `game/nba` returns 200.
2. Run `tester.py` to get the 2026-27 `league_key` (`{game_key}.l.{league_id}`) and verify team keys. Then write `refresh_token`, `auth_code`, and `zeta_ball_2026_2027_league_key` to the secret (confirm with Connor before writing).
3. Update season-specific values:
   - `aws_iac_mngr/.../zeta-ball-api-to-sf/constants.py`: `LEAGUE_KEY`, `SEASON_START_WEEK = '2026-10-19'`, `TEAM_KEYS`; rebuild zip (`build-lambda-zip.sh`) and `tofu apply` in `controlled_resources/lambda/`.
   - `connors_snowflake_db/.../stg/procedure/refresh_weekly.sql`: `TO_DATE('2026-10-19')` and the hardcoded `team_key_list`; re-run `CREATE OR REPLACE PROCEDURE`.
   - `connors_snowflake_db/.../dwh/table/teams.sql`: re-seed with new team keys.
4. Truncate last season's rows in `DWH.WEEKLY_TEAM_TOTALS` and `DWH.MATCHUPS_CROSSJOIN` (Connor said he'd do this) — week numbers collide across seasons.
5. Resume the task: `ALTER TASK STG.REFRESH_WEEKLY_TASK RESUME`.

**Season timing:** week 1 is Mon 2026-10-19 – Sun 10-25. First scheduled run Mon 2026-10-26 pulls week 1 (WEEK_NUMBER = 1). If approval arrives late, `REFRESH_WEEKLY` only pulls the week computed from today's date; backfilling missed weeks needs a procedure change (e.g. an optional week parameter).
