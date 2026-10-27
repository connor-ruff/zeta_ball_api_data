# zeta_ball_api_data — Project Home Base

This repo is the "home base" for the Zeta Ball API data project. The project spans three repos, all under `/Users/connor/source/repos/`. Sessions are started from this repo with the other two added as additional working directories (see `bin/claude-proj-start.sh`).

## Repos in this project

| Repo | Role |
|------|------|
| `zeta_ball_api_data` (this repo) | API-side work: auth and testing scripts for both Yahoo and Walter APIs (`manual_scripts/`) and analysis SQL (`queries/`). |
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

## STATUS: ACTIVE on Walter's API (as of 2026-10-24) — Yahoo path on hold pending approval

The weekly refresh now reads from Walter's League Data API (`https://www.zetaball.com/api/v1`, league id `zeta_ball`), not Yahoo. Plan: run on Walter's API until Yahoo approves the app, then possibly switch back.

**Why Yahoo is on hold**
- Re-authorizing works (token exchange 200), but every Yahoo Fantasy API call returns `403 This application is not authorized to perform this action` (even `game/nba`). The token is valid; the *app* isn't authorized. Same with old and brand-new apps.
- Likely cause: Yahoo's application/approval step (https://sports.yahoo.com/developer/application-confirmation/). Connor submitted it for the new app on 2026-10-19. Not confirmed.
- Yahoo secret `yahoo-fantasy--slop-api-keys` has new `app_id`/`client_id`/`client_secret`; `auth_code`, `refresh_token`, `zeta_ball_2026_2027_league_key` intentionally BLANK. Values aren't managed by OpenTofu (container only).

**Current pipeline (Walter)** — separate infra, all named `*_WALTER_*` / `walter`:
- Snowflake (`connors_snowflake_db/snowflake_objects/zeta_ball/`):
  - `STG.REFRESH_WEEKLY_TASK` (Mon 8 PM ET) calls `STG.REFRESH_WEEKLY_WALTER()`. The task file ends with `RESUME`; verify actual task state in Snowflake rather than assuming.
  - `STG.REFRESH_WEEKLY_WALTER()` first calls `STG.REFRESH_TEAMS_WALTER()` (updates `DWH.TEAMS.YAHOO_TEAM_NAME`), then pulls the week's matchups, loads `STG.WEEKLY_MATCHUPS_WALTER_RAW` → `STG.WEEKLY_MATCHUP_CATEGORY_STATS_WALTER`, then rebuilds that week's rows in `DWH.WEEKLY_TEAM_TOTALS` and `DWH.MATCHUPS_CROSSJOIN`. Deletes-then-inserts per season+week, so reruns are safe and old seasons are not truncated.
  - Season and week are derived from `DWH.LEAGUES` (`YEAR(MAX(WEEK_1_START_DATE))`, `DATEDIFF('WEEK', ...)`). Only the current week is pulled; errors if the week is < 1. No backfill parameter yet.
  - External function `STG.ZETA_BALL_WALTER_REFRESH_LAMBDA_TRIGGER(refresh_type_id, input1..5)`: type 1 = matchups (season, week), type 2 = teams (season). Stage `STG.ZETA_BALL_WALTER_STAGE`.
  - Walter's API does not provide FGM/FGA/FTM/FTA; only `FG_PCT`/`FT_PCT` are populated in `DWH.WEEKLY_TEAM_TOTALS`.
- AWS (`aws_iac_mngr/controlled_resources/`): Lambda `lambda-zeta-ball-walter-api-to-sf` (source in `lambda/function_code/zeta-ball-walter-api-to-sf/`), API Gateway route `route_zeta_ball_walter.tf`, IAM `lambda_zeta_ball_walter.tf`, secret `zetaball-walter-api-key` (`bsbk_...` bearer key).
- Local: `manual_scripts/walt_test.py` hits the Walter endpoints and dumps JSON to `manual_scripts/walt_output/`.

**Public SlopCS website** — http://zeta-ball-slopcs.s3-website.us-east-2.amazonaws.com
- **The SlopCS algorithm is proprietary.** Publish only rank, team, and SlopCS score. Never show or publish how it's computed (no W-L-T records, category results, or explanatory text) on the page or in the public JSON.
- S3 bucket `zeta-ball-slopcs` (public read, plain S3 website, no CloudFront). `index.html` lives in `aws_iac_mngr/controlled_resources/general/s3/site_content/zeta-ball-slopcs/` and deploys via `tofu apply` in `general/s3/`. Published scores are win% x 10000, 2 decimals (scaled in `STG.PUBLISH_SLOPCS`).
- After its commit, `STG.REFRESH_WEEKLY_WALTER` calls `STG.PUBLISH_SLOPCS()`, which unloads `data/latest.json` and `data/season_{yr}/week_{n}.json` via `STG.SLOPCS_SITE_STAGE`, reading from the `DWH.SLOP_CS_RANKINGS_BY_WEEK` view.

**Reorganized dimensions (DWH)**
- `DWH.LEAGUES`: one row per season (`LEAGUE_START_YEAR`, `WEEK_1_START_DATE`, `YAHOO_NBA_SEASON_KEY`, `YAHOO_LEAGUE_KEY`). 2026 row: start 2026-10-19, season key 478, league 19581. **Adding a new season row here is what advances the pipeline.**
- `DWH.LEAGUE_MEMBERS`: `LEAGUE_MEMBER_SID` → `MANAGER` (stable across seasons).
- `DWH.TEAMS`: one row per member per season (`TEAM_SID`, `LEAGUE_START_YEAR`, `LEAGUE_MEMBER_SID`, `YAHOO_TEAM_ID`, `YAHOO_TEAM_NAME`). Walter's `team_id` is the Yahoo team id; the pipeline joins on season + `YAHOO_TEAM_ID`. 2026 team ids are the same as 2025.
- `DWH.TEAMS_FULL` view joins the three and builds `YAHOO_TEAM_KEY`.
- Fact tables key on `TEAM_SID` + `LEAGUE_START_YEAR`, so seasons coexist.

**If switching back to Yahoo once approved** (the old Yahoo objects still exist: `STG.REFRESH_WEEKLY`, Lambda `lambda-zeta-ball-api-to-sf`, `zeta-ball-refresh` external function; the Yahoo procedure may be stale against the reorganized dimensions, so review before use):
1. Re-run OAuth: auth URL from the secret's `client_id`/`redirect_uri` (scope `fspt-r`), exchange the `code=` value (expires in minutes). Confirm `game/nba` returns 200.
2. Run `manual_scripts/tester.py` (`list_my_nba_leagues()`, `get_league_teams()`, `check_league_and_team_keys()`) to verify league/team keys, then write `refresh_token`, `auth_code`, `zeta_ball_2026_2027_league_key` to the secret (confirm with Connor first).
3. Update season-specific values in `zeta-ball-api-to-sf/constants.py` (`LEAGUE_KEY`, `SEASON_START_WEEK`, `TEAM_KEYS`; rebuild zip, `tofu apply` in `controlled_resources/lambda/`) and in `stg/procedure/refresh_weekly.sql` (hardcoded date and `team_key_list`).
4. Point `STG.REFRESH_WEEKLY_TASK` at `STG.REFRESH_WEEKLY` instead of the Walter procedure.

Notes: EventBridge schedule `zeta-ball-api-pull` is an unused relic; leave disabled.

**Season timing:** week 1 is Mon 2026-10-19 – Sun 10-25. First scheduled run Mon 2026-10-26 pulls week 1.
