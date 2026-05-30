"""
Games Endpoints

Games list page. One endpoint returns the games for a (season, league, week)
plus the available seasons/weeks for the filter bar. When season_id / week_id
are omitted they resolve to the latest season and the latest week that has
played results (league 37 is the frontend default).
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.games import GamesPage, GameTeamStats, GameSkaterStats, GameGoalieStats
from app.schemas.games import (
    GameRow, TeamSide, WeekOption, DayOption, GamesResponse,
    TeamBreakdown, SkaterLine, GoalieLine, GameDetailResponse,
)
from app.util.helpers import validate_param

router = APIRouter()

S3 = "https://spreadsheet-hockey-logos.s3.us-east-1.amazonaws.com"


def _logo(full_name: str | None) -> str | None:
    return f"{S3}/{full_name.replace(' ', '%20')}.png" if full_name else None


def _game_row(g: GamesPage) -> GameRow:
    return GameRow(
        game_id=g.game_id,
        week_id=g.week_id,
        game_datetime=g.game_datetime,
        home=TeamSide(
            id=g.home_team_id, name=g.home_team_name, full_name=g.home_team_full_name,
            color=g.home_team_color, logo_path=_logo(g.home_team_full_name), score=g.home_score,
        ),
        away=TeamSide(
            id=g.away_team_id, name=g.away_team_name, full_name=g.away_team_full_name,
            color=g.away_team_color, logo_path=_logo(g.away_team_full_name), score=g.away_score,
        ),
        winner=g.winner,
        is_overtime=bool(g.is_overtime),
        is_forfeit=bool(g.is_forfeit),
        is_final=bool(g.is_final),
    )


@router.get("/cards", response_model=GamesResponse)
async def get_games(
    league_id: int,
    game_type_id: int = 1,
    season_id: int | None = None,
    week_id: int | None = None,
    game_date: str | None = None,
    page_number: int = 1,
    page_size: int = 200,
    session: AsyncSession = Depends(get_db),
):
    # NOTE: public endpoint (no auth). Games schedule + final scores are public
    # info (not premium analytics). Gate with require_auth if that changes.
    if not validate_param("league_id", league_id, allowed_values=[37, 38, 84, 39, 112]):
        raise HTTPException(status_code=400, detail="Invalid league_id")
    if not validate_param("game_type_id", game_type_id, allowed_values=[1, 2]):
        raise HTTPException(status_code=400, detail="Invalid game_type_id")
    if not validate_param("page_number", page_number, gt=0):
        raise HTTPException(status_code=400, detail="Invalid page_number")
    page_size = max(1, min(page_size, 500))

    base = [GamesPage.league_id == league_id, GamesPage.game_type_id == game_type_id]

    # available seasons (desc)
    seasons = [
        r[0] for r in (await session.execute(
            select(distinct(GamesPage.season_id)).where(*base).order_by(GamesPage.season_id.desc())
        )).all()
    ]
    if not seasons:
        return GamesResponse(
            data=[], season_id=season_id or 0, league_id=league_id, game_type_id=game_type_id,
            week_id=0, game_date=None, seasons=[], weeks=[], days=[], total=0, page_number=page_number,
            page_size=page_size, total_pages=0, last_updated="N/A",
        )

    # resolve season -> latest if not given
    if season_id is None:
        season_id = seasons[0]
    elif not validate_param("season_id", season_id, gt=45, lt=60):
        raise HTTPException(status_code=400, detail="Invalid season_id")

    season_filter = base + [GamesPage.season_id == season_id]

    # weeks for the resolved season (with played / scheduled counts)
    week_rows = (await session.execute(
        select(
            GamesPage.week_id,
            func.count().filter(GamesPage.is_final.is_(True)).label("played"),
            func.count().filter(GamesPage.is_final.is_(False)).label("scheduled"),
        ).where(*season_filter).group_by(GamesPage.week_id).order_by(GamesPage.week_id)
    )).all()
    weeks = [WeekOption(week_id=w, played=p, scheduled=s) for (w, p, s) in week_rows if w is not None]

    # resolve week -> latest with played results, else latest overall
    if week_id is None:
        played_weeks = [w.week_id for w in weeks if w.played > 0]
        week_id = max(played_weeks) if played_weeks else (weeks[-1].week_id if weeks else 0)

    week_filter = season_filter + [GamesPage.week_id == week_id]

    # days that have completed games in this week (scheduled games have no date)
    day_rows = (await session.execute(
        select(GamesPage.game_date, func.count().label("played"))
        .where(*week_filter, GamesPage.game_date.isnot(None), GamesPage.is_final.is_(True))
        .group_by(GamesPage.game_date).order_by(GamesPage.game_date)
    )).all()
    days = [DayOption(date=d.isoformat(), label=d.strftime("%A"), played=p) for (d, p) in day_rows]

    # resolve day -> provided value, else the latest day with completed games
    resolved_day: date | None = None
    if game_date:
        try:
            resolved_day = date.fromisoformat(game_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid game_date (expected YYYY-MM-DD)")
    elif days:
        resolved_day = date.fromisoformat(days[-1].date)

    game_filter = list(week_filter)
    if resolved_day is not None:
        game_filter.append(GamesPage.game_date == resolved_day)

    total = (await session.execute(
        select(func.count()).select_from(GamesPage).where(*game_filter)
    )).scalar() or 0

    rows = (await session.execute(
        select(GamesPage).where(*game_filter)
        .order_by(GamesPage.game_datetime.asc().nullslast(), GamesPage.game_id.asc())
        .offset((page_number - 1) * page_size).limit(page_size)
    )).scalars().all()

    data = [_game_row(g) for g in rows]

    last_updated = "N/A"
    if rows and rows[-1].last_updated:
        last_updated = rows[-1].last_updated.strftime("%Y-%m-%d")

    return GamesResponse(
        data=data,
        season_id=season_id,
        league_id=league_id,
        game_type_id=game_type_id,
        week_id=week_id,
        game_date=resolved_day.isoformat() if resolved_day else None,
        seasons=seasons,
        weeks=weeks,
        days=days,
        total=total,
        page_number=page_number,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
        last_updated=last_updated,
    )


@router.get("/{game_id}", response_model=GameDetailResponse)
async def get_game_detail(
    game_id: int,
    session: AsyncSession = Depends(get_db),
):
    """Full breakdown for a single game: header, team comparison, skaters, goalies. Public."""
    header_row = (await session.execute(
        select(GamesPage).where(GamesPage.game_id == game_id)
    )).scalar_one_or_none()
    if header_row is None:
        raise HTTPException(status_code=404, detail="Game not found")

    home_id = header_row.home_team_id
    away_id = header_row.away_team_id

    # team breakdowns
    team_rows = (await session.execute(
        select(GameTeamStats).where(GameTeamStats.game_id == game_id)
    )).scalars().all()

    def team_breakdown(t: GameTeamStats) -> TeamBreakdown:
        return TeamBreakdown(
            team_id=t.team_id, team_name=t.team_name, full_team_name=t.full_team_name,
            team_color=t.team_color, logo_path=_logo(t.full_team_name),
            is_home=bool(t.is_home), score=t.score,
            team_wins=t.team_wins, team_losses=t.team_losses, team_otl=t.team_otl,
            p1g=t.p1g or 0, p2g=t.p2g or 0, p3g=t.p3g or 0, otg=t.otg or 0,
            is_overtime=bool(t.is_overtime), win=t.win, loss=t.loss, otl=t.otl,
            goals=t.goals, shots=t.shots, shots_against=t.shots_against, hits=t.hits, toa=t.toa,
            fow=t.fow, fol=t.fol, pim=t.pim, ppg=t.ppg, ppa=t.ppa, blocks=t.blocks,
            takeaways=t.takeaways, giveaways=t.giveaways, interceptions=t.interceptions,
            pk_clears=t.pk_clears, shg=t.shg, passes=t.passes, passes_att=t.passes_att, saves=t.saves,
            total_gar=t.total_gar, offensive_gar=t.offensive_gar, defensive_gar=t.defensive_gar,
            total_xg=t.total_xg, opponent_xg=t.opponent_xg,
        )

    home_team = next((team_breakdown(t) for t in team_rows if t.team_id == home_id), None)
    away_team = next((team_breakdown(t) for t in team_rows if t.team_id == away_id), None)

    # skaters (ordered by points, then GAR)
    skater_rows = (await session.execute(
        select(GameSkaterStats).where(GameSkaterStats.game_id == game_id)
        .order_by(GameSkaterStats.points.desc().nullslast(), GameSkaterStats.total_gar.desc().nullslast())
    )).scalars().all()

    def skater_line(s: GameSkaterStats) -> SkaterLine:
        return SkaterLine(
            player_id=s.player_id, player_name=s.player_name, team_id=s.team_id,
            position=s.position, pos_group=s.pos_group, toi=s.toi,
            points=s.points, goals=s.goals, assists=s.assists, plus_minus=s.plus_minus,
            shots=s.shots, hits=s.hits, takeaways=s.takeaways, giveaways=s.giveaways,
            blocks=s.blocks, interceptions=s.interceptions, pim=s.pim, ppg=s.ppg, shg=s.shg,
            gwg=s.gwg, fow=s.fow, fol=s.fol,
            total_gar=s.total_gar, offensive_gar=s.offensive_gar, defensive_gar=s.defensive_gar,
            xg=s.xg, xa=s.xa, ovr=s.ovr, off_rating=s.off_rating, def_rating=s.def_rating,
        )

    # goalies (ordered by TOI, starter first)
    goalie_rows = (await session.execute(
        select(GameGoalieStats).where(GameGoalieStats.game_id == game_id)
        .order_by(GameGoalieStats.toi.desc().nullslast())
    )).scalars().all()

    def goalie_line(g: GameGoalieStats) -> GoalieLine:
        return GoalieLine(
            player_id=g.player_id, player_name=g.player_name, team_id=g.team_id, toi=g.toi,
            shots_against=g.shots_against, saves=g.saves, goals_against=g.goals_against,
            sv_pct=g.sv_pct, gaa=g.gaa, shutouts=g.shutouts, gsax=g.gsax, gsaa=g.gsaa,
        )

    return GameDetailResponse(
        header=_game_row(header_row),
        home_team=home_team,
        away_team=away_team,
        home_skaters=[skater_line(s) for s in skater_rows if s.team_id == home_id],
        away_skaters=[skater_line(s) for s in skater_rows if s.team_id == away_id],
        home_goalies=[goalie_line(g) for g in goalie_rows if g.team_id == home_id],
        away_goalies=[goalie_line(g) for g in goalie_rows if g.team_id == away_id],
    )
