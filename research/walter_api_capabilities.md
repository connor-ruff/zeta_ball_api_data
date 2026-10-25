# Walter's League Data API: what's possible (trade analyzer research)

*Researched 2026-10-24. Sources: the full API guide (`GET https://www.zetaball.com/api/v1/docs`, a single Markdown page), the OpenAPI spec (`/api/v1/openapi.json`), and live read-only calls against `zeta_ball` with our key.*

## TL;DR

- **Rosters and player stats are covered well.** Every team's roster is synced from Yahoo every 15 minutes. Every player has per-game averages over 7, 14 and 30 days, a 30-day game log, the upcoming schedule (games in the next N days, back-to-backs) and injury status. `fga`/`fta` are included, so FG% and FT% can be weighted by volume properly.
- **There are no player projections.** The only projection-like data is `/outlook`, which estimates the rest of the current week for your own matchup from recent averages. Anything forward-looking we have to build ourselves.
- **Player stats are only a rolling 30 days.** `/players` takes no `season` parameter, and the game log covers only the last 30 days. **To get season-long per-player data, we have to collect it ourselves, starting soon.** Week 1 games (from 10/20) start dropping out of the 30-day window around **11/19**.
- **Walter already grades trades and drafts after the fact.** `/trades` replays every trade in league history (117 for Zeta Ball) and scores each side by expected matchup wins gained or lost. That's a useful benchmark and validation set for our own analyzer, which would look *forward* instead.
- **There's a lot of league history.** Category totals for every matchup go back to 2022, when the league switched to 9-cat; 2018–2021 were points leagues. There are also standings with luck and expected wins, manager career profiles with Elo, and draft grades.

## Endpoint map

All are `GET` and read-only. Paths are under `https://www.zetaball.com/api/v1`, and league paths are under `/leagues/zeta_ball`. Auth is `Authorization: Bearer bsbk_...`, with a limit of 120 requests per minute per key. Every list endpoint also takes `format=csv`.

| Endpoint | What it gives | Useful for |
|---|---|---|
| `/me`, `/leagues`, `/leagues/{id}`, `/settings` | Your manager id (`zb:Connor`); categories and their direction; lineup slots (G,G,F,F,C,Util×3,BN×2,IL×2); 18 teams; season window 2026-10-20 → 2027-04-20 | Config, lineup rules |
| `/teams?season=` | Managers and team names per season. `team_id` (Yahoo team #) is only set for the live season | Already used (`REFRESH_TEAMS_WALTER`) |
| `/matchups?season=&week=&manager=&status=` | Head-to-head matchups with 9-cat totals for both sides. `week=all` works, and so does history back to 2018 | Already used; **historical backfill** |
| `/outlook?manager=&window=` | **Live current-week** matchup: each category now and projected to week's end, games left per side, each player's games left | Weekly streaming and lineup decisions |
| `/weeks/report?season=&week=` | Week summary: rank, all-play record, lucky wins, heartbreaks, closest game, category leaders | Weekly recap content |
| `/weeks/all-play?manager=&week=` | One team against every other team that week, category by category, plus that team's rank in each category | Category strengths and weaknesses |
| `/standings?season=` | Record, category record, all-play record, `expected_wins`, `luck_wins`, playoff seed, moves, trades. Published nightly, completed weeks only | Season context |
| `/head-to-head?opponent=` | All-time series against one manager, split into points and categories eras | Fun |
| `/managers/{m}` | Career record, titles, all-play %, luck, **Elo**, best and worst seasons | Fun |
| `/rosters?manager=&include_stats=true` | Every roster: player, lineup slot, injury status, % rostered (Yahoo and ESPN). With `include_stats`, adds `recent` averages and `schedule` | **Core trade-analyzer input** |
| `/players?search=&team=&position=&owner=&window=&min=&max=&sort=&limit=` | Every player in the league's pool (rostered, free agent, or "available"), with `recent` and `schedule`. Can filter by stat thresholds | **Core: player universe** |
| `/players/{player_key}` | One player, plus `game_log`: every game in the last 30 days with a full stat line | **Core: build our own history** |
| `/free-agents?position=&window=&min=&sort=&limit=` | Top 300 unrostered players ranked by Yahoo's actual rank, with recent stats, schedule, and waiver vs free-agent status | Replacement level; waiver wire |
| `/transactions?manager=&type=&since=` | Adds, drops and trades for the **current season** (refreshed about hourly). Past seasons come back empty for Zeta Ball | Roster churn; trade detection |
| `/trades?season=&manager=&sort=` | **Every trade in league history, graded**: `delta_wins`, z-score, Won/Lost/Wash, a "stakes" grade, stretch-run flag | **Benchmark for our analyzer** |
| `/draft?season=` | Auction draft (2025 and 2026 are auctions), every pick graded: cost, value (9-cat z), steal/bust | Fun; season-start values |
| `/games?sport=basketball&date=` or `from=&to=` | Real NBA schedule and scores. `pro_team` codes match the rosters | Games remaining per player |
| `/documents` | League constitution and rules docs (none posted for Zeta Ball) | none |

There's also a hosted **MCP server** at `https://www.zetaball.com/api/mcp` that exposes the same endpoints as tools, plus ready-made prompts: `trade_check`, `waiver_wire_report`, `lineup_check`, `scouting_report` and `weekly_recap`. It could be connected to Claude Code (`claude mcp add --transport http league https://www.zetaball.com/api/mcp`) for quick questions without writing any code. Worth trying as a baseline before building anything.

## What I verified live (2026-10-24)

- **Player stat shape:** `recent.{7d,14d,30d}` has `games` plus per-game `minutes, fg_pct, ft_pct, fga, fta, tpm, pts, reb, ast, stl, blk, tov`. The docs list `fga`/`fta` only in some places, but they're present in the real responses. Game log entries carry the same keys for one game.
- **Size of the player pool:** `/players?limit=500` returned 500 rows with `meta.matched = 604`. **500 is the per-call cap and there's no offset or paging parameter.** To get everyone, split the calls with filters, e.g. `owner=available`, plus `owner=<manager>` per team, or by `position`. I haven't tested this, but the filters are documented.
- **No player history:** passing `season` to `/players` or `/players/{key}` is rejected with `unknown_parameter`. Player stats exist only as rolling windows and the 30-day game log.
- **Player keys** look like `478.p.6514`. Yahoo's game-key prefix changes every season (2025 was `466`, 2026 is `478`), so join across seasons on the numeric id after `.p.`.
- **My roster today:** 11 players, including Luka Dončić, Zach LaVine, Ivica Zubac, Josh Hart and Andrew Wiggins. Jimmy Butler has 0 games so far.
- **Matchup history:** `matchups?season=2025&week=all&status=final&format=csv` returns 348 rows, one row per team per matchup with every category for both sides. 2022 week 1 also returns 9-cat data.
- **Trades:** 117 graded trades across league history. The biggest so far is Walter getting Jamal Murray for Garland and Oubre in 2025, at +1.57 expected wins.
- **Outlook:** works for the live week. It projects counting stats only; FG% and FT% aren't projected.
- **Standings:** 2025 includes `expected_wins` and `luck_wins`. For example, the 17-1 team was +5.0 luck wins.

## Gaps and how to fill them

| Need for a trade analyzer | Available? | How to fill |
|---|---|---|
| Who's on each roster, with eligible positions and slot | ✅ `/rosters` | Pull it directly |
| Recent per-game production | ✅ 7/14/30-day windows | Pull it directly |
| Season-to-date per-player stats | ❌ (30 days max) | **Snapshot game logs into Snowflake** (see below) |
| Rest-of-season projections | ❌ | Build our own (see "Projections") |
| Games remaining per player | ✅ partly: `schedule.games_next_days` covers 7 days; `/games` covers the full NBA schedule | Count remaining games per `pro_team` from `/games?from=&to=` (31 days per call, so loop) |
| Injury status | ✅ `status`, `injury_note` | Pull it; discount injured players manually |
| Replacement level (what a freed roster spot is worth) | ✅ `/free-agents` | Value of the best free agent at the position |
| League-wide category distribution (to turn stats into wins) | ✅ our `DWH.WEEKLY_TEAM_TOTALS` plus history | Already have it |
| Ground truth for checking our analyzer | ✅ `/trades` (117 graded trades) | Compare our verdicts with Walter's |

## Projections: options

There's no projection feed, so the choice is a tradeoff between effort and quality:

1. **Blend recent windows (easiest).** For example, 0.2×7d + 0.3×14d + 0.5×30d per-game averages. That covers most of the signal for an in-season trade. It doesn't handle injuries returning or role changes.
2. **Our own season-to-date plus a prior (best long-term).** Snapshot game logs nightly so we have the full season, then weight season-to-date against recent form. A prior from last season would need a one-time external pull, because Walter has no player history.
3. **External projections.** Paid sources (Hashtag Basketball, Basketball Monster) and scraping both raise terms-of-service issues. The NBA's stats site has an unofficial API, but it's flaky and rate-limited. If the Yahoo app is approved, Yahoo's API has season and last-N stats per player; I haven't confirmed whether it exposes projections. I'd skip this to start.

My recommendation is option 1 now and option 2 once a few weeks of game logs have been collected.

## How a trade analyzer could work

The standard 9-cat approach, made specific to our league:

1. **Per-player value:** compute per-game z-scores per category against the league's rostered player pool. FG% and FT% get impact-weighted: `fga × (fg_pct − league_avg)`, not raw percentage, which is why `fga`/`fta` matter. Turnovers are reversed. Walter's draft grades use the same "summed per-game 9-cat z" approach, so the numbers would be comparable.
2. **Team before and after:** project each affected team's weekly category totals from per-game rates × expected games. Account for the lineup limit too: 8 starting slots per day means extra bodies don't all count.
3. **Turn stats into wins:** compare the projected weekly totals against the actual distribution of weekly team totals in our league (from `DWH.WEEKLY_TEAM_TOTALS`). Estimate the probability of winning each category against each of the other 17 teams, then sum. The output is **expected category wins per week**, before vs. after. This is roughly what Walter's trade grade measures looking back.
4. **Roster spots:** in a 2-for-1, the side receiving one player gets an open spot worth the best free agent at a position (from `/free-agents`). Without this, 2-for-1s always look lopsided.
5. **Explain the result:** show the category-by-category change, e.g. "+1.2 BLK wins, −0.8 FT% wins". Also flag punt fits: a trade that hurts a category you're already punting costs nothing.

## Suggested architecture (reusing what we have)

This uses the same pattern as the SlopCS pipeline: Snowflake external function → Lambda → S3 → `COPY INTO`.

- **Lambda:** add new `refresh_type_id`s to `lambda-zeta-ball-walter-api-to-sf`:
  - `3` = player universe snapshot (`/players`, split by filters to get past the 500 cap)
  - `4` = player game logs (`/players/{key}` for rostered and top free-agent players: about 250–600 calls, 2–5 minutes at 120/min; under Lambda's 15-minute max, but the timeout would need raising from 1 minute)
  - `5` = rosters (`/rosters?include_stats=true`, 1 call)
  - `6` = transactions since a date
- **Snowflake (new tables):**
  - `DWH.PLAYERS` (dimension on the numeric player id: name, positions, pro team)
  - `DWH.PLAYER_GAME_LOGS` (player × date; merge on that key so overlapping 30-day pulls deduplicate)
  - `DWH.ROSTER_SNAPSHOTS` (date × manager × player × slot)
  - `DWH.TRANSACTIONS`
- **Schedule:** a nightly or every-few-days task for game logs and rosters, separate from the Monday SlopCS task. Because the game log overlaps 30 days, a pull every few days loses nothing and can recover from failures.
- **Analyzer UI:** this tool is internal, so **Streamlit in Snowflake** fits well. Its downside (requiring a Snowflake login) doesn't matter here, and it reads the tables directly with no new infrastructure. Simpler options: a Python script or notebook, or a Snowflake UDTF like `TRADE_EVAL(give ARRAY, get ARRAY, partner VARCHAR)`.

## Side wins found along the way

- **SlopCS history backfill:** `/matchups?season=X&week=all&status=final` has category totals for 2022–2025, so `WEEKLY_TEAM_TOTALS` and `MATCHUPS_CROSSJOIN` could be backfilled for earlier seasons. That would give multi-season SlopCS history and a better category distribution for step 3 above. It needs `DWH.LEAGUES` and `DWH.TEAMS` rows for those seasons, since `team_id` is null for past seasons, so join on `manager`.
- **Cross-checks:** Walter's API includes all-play records (`/weeks/report`, `/weeks/all-play`, `/standings`). These could validate our weekly loads.
- **Luck and Elo:** `luck_wins` and manager Elo are available in case the league page ever wants more content. Those come from Walter, not SlopCS.

## Suggested next steps (in order)

1. **Start collecting player game logs before about 11/19**, when week 1 drops out of the 30-day window. Even a crude nightly dump to S3 would preserve the data while the rest gets designed.
2. Try Walter's MCP `trade_check` prompt in Claude Code for a zero-code baseline.
3. Build the player value model (z-scores from the 14-day and 30-day windows) as a Snowflake view.
4. Build the before/after expected-category-wins evaluation and check it against Walter's graded trades from 2025.
5. Optionally, put a small Streamlit-in-Snowflake UI on top.
