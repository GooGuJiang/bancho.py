"""自定义谱面成绩的数据库操作"""

from __future__ import annotations

from datetime import datetime

# 自定义成绩的 TypedDict 类型
from typing import Any
from typing import List
from typing import Optional
from typing import TypedDict
from typing import cast

from sqlalchemy import delete
from sqlalchemy import func
from sqlalchemy import insert
from sqlalchemy import select
from sqlalchemy import text
from sqlalchemy import update

import app.state.services


class CustomScore(TypedDict):
    id: int
    map_id: int
    map_md5: str
    user_id: int
    score: int
    pp: float
    acc: float
    max_combo: int
    mods: int
    n300: int
    n100: int
    n50: int
    nmiss: int
    ngeki: int
    nkatu: int
    grade: str
    status: int  # 0=failed, 1=submitted, 2=best
    mode: int
    play_time: datetime
    time_elapsed: int
    client_flags: int
    perfect: bool
    online_checksum: str


async def create(
    map_id: int,
    map_md5: str,
    user_id: int,
    score: int,
    pp: float,
    acc: float,
    max_combo: int,
    mods: int,
    n300: int,
    n100: int,
    n50: int,
    nmiss: int,
    ngeki: int,
    nkatu: int,
    grade: str,
    status: int,
    mode: int,
    play_time: datetime,
    time_elapsed: int,
    client_flags: int,
    perfect: bool,
    online_checksum: str,
) -> int:
    """创建新的自定义成绩记录"""

    query = text(
        """
        INSERT INTO custom_scores
        (map_id, map_md5, user_id, score, pp, acc, max_combo, mods,
         n300, n100, n50, nmiss, ngeki, nkatu, grade, status, mode,
         play_time, time_elapsed, client_flags, perfect, online_checksum)
        VALUES (:map_id, :map_md5, :user_id, :score, :pp, :acc, :max_combo, :mods,
                :n300, :n100, :n50, :nmiss, :ngeki, :nkatu, :grade, :status, :mode,
                :play_time, :time_elapsed, :client_flags, :perfect, :online_checksum)
    """,
    )

    score_id = await app.state.services.database.execute(
        """
    INSERT INTO custom_scores VALUES (
        NULL,
        :map_id, :map_md5, :user_id, :score,
        :pp, :acc, :max_combo, :mods,
        :n300, :n100, :n50, :nmiss,
        :ngeki, :nkatu, :grade, :status,
        :mode, :play_time, :time_elapsed,
        :client_flags, :perfect, :online_checksum
    )
    """,
        {
            "map_id": map_id,
            "map_md5": map_md5,
            "user_id": user_id,
            "score": score,
            "pp": pp,
            "acc": acc,
            "max_combo": max_combo,
            "mods": mods,
            "n300": n300,
            "n100": n100,
            "n50": n50,
            "nmiss": nmiss,
            "ngeki": ngeki,
            "nkatu": nkatu,
            "grade": grade,
            "status": status,
            "mode": mode,
            "play_time": play_time,
            "time_elapsed": time_elapsed,
            "client_flags": client_flags,
            "perfect": int(perfect),
            "online_checksum": online_checksum,
        },
    )

    return cast(int, score_id)


async def fetch_one(
    score_id: int | None = None,
    map_md5: str | None = None,
    user_id: int | None = None,
    mode: int | None = None,
    status: int | None = None,
) -> CustomScore | None:
    """获取单个自定义成绩"""

    conditions = []
    params = {}

    if score_id is not None:
        conditions.append("id = :score_id")
        params["score_id"] = score_id

    if map_md5 is not None:
        conditions.append("map_md5 = :map_md5")
        params["map_md5"] = map_md5

    if user_id is not None:
        conditions.append("user_id = :user_id")
        params["user_id"] = user_id

    if mode is not None:
        conditions.append("mode = :mode")
        params["mode"] = mode

    if status is not None:
        conditions.append("status = :status")
        params["status"] = status

    if not conditions:
        return None

    where_clause = " AND ".join(conditions)
    query = text(
        f"SELECT * FROM custom_scores WHERE {where_clause} ORDER BY score DESC LIMIT 1",
    )

    result = await app.state.services.database.fetch_one(query, params)
    return cast(CustomScore, result) if result else None


async def fetch_many(
    map_md5: str | None = None,
    user_id: int | None = None,
    mode: int | None = None,
    status: int | None = None,
    limit: int = 50,
) -> list[CustomScore]:
    """获取多个自定义成绩"""

    conditions = []
    params: dict[str, Any] = {"limit": limit}

    if map_md5 is not None:
        conditions.append("map_md5 = :map_md5")
        params["map_md5"] = map_md5

    if user_id is not None:
        conditions.append("user_id = :user_id")
        params["user_id"] = user_id

    if mode is not None:
        conditions.append("mode = :mode")
        params["mode"] = mode

    if status is not None:
        conditions.append("status = :status")
        params["status"] = status

    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
    query = text(
        f"SELECT * FROM custom_scores {where_clause} ORDER BY score DESC LIMIT :limit",
    )

    results = await app.state.services.database.fetch_all(query, params)
    return [cast(CustomScore, result) for result in results]


async def update_status(
    score_id: int,
    status: int,
) -> bool:
    """更新成绩状态"""

    query = text("UPDATE custom_scores SET status = :status WHERE id = :score_id")
    await app.state.services.database.execute(
        query,
        {"status": status, "score_id": score_id},
    )
    return True


async def update_previous_best(
    map_md5: str,
    user_id: int,
    mode: int,
    exclude_score_id: int | None = None,
) -> bool:
    """将之前的最佳成绩状态改为已提交"""

    conditions = [
        "map_md5 = :map_md5",
        "user_id = :user_id",
        "mode = :mode",
        "status = 2",
    ]
    params = {"map_md5": map_md5, "user_id": user_id, "mode": mode}

    if exclude_score_id is not None:
        conditions.append("id != :exclude_score_id")
        params["exclude_score_id"] = exclude_score_id

    where_clause = " AND ".join(conditions)
    query = text(f"UPDATE custom_scores SET status = 1 WHERE {where_clause}")

    await app.state.services.database.execute(query, params)
    return True


async def get_user_rank_on_map(
    map_md5: str,
    user_id: int,
    mode: int,
    score_value: int,
) -> int:
    """获取用户在谱面上的排名"""

    query = text(
        """
        SELECT COUNT(*) + 1 as rank
        FROM custom_scores cs
        INNER JOIN users u ON cs.user_id = u.id
        WHERE cs.map_md5 = :map_md5
        AND cs.mode = :mode
        AND cs.status = 2
        AND u.priv & 1
        AND cs.score > :score_value
    """,
    )

    result = await app.state.services.database.fetch_one(
        query,
        {"map_md5": map_md5, "mode": mode, "score_value": score_value},
    )

    return result["rank"] if result else 1


async def get_leaderboard_scores(
    map_md5: str,
    mode: int,
    mods: int | None = None,
    limit: int = 50,
) -> list[dict]:
    """获取谱面排行榜成绩"""

    conditions = [
        "cs.map_md5 = :map_md5",
        "cs.mode = :mode",
        "cs.status = 2",
        "u.priv & 1",
    ]
    params = {"map_md5": map_md5, "mode": mode, "limit": limit}

    if mods is not None:
        conditions.append("cs.mods = :mods")
        params["mods"] = mods

    where_clause = " AND ".join(conditions)

    query = text(
        f"""
        SELECT cs.id, cs.score, cs.max_combo, cs.n50, cs.n100, cs.n300,
               cs.nmiss, cs.nkatu, cs.ngeki, cs.mods, cs.pp,
               UNIX_TIMESTAMP(cs.play_time) as time,
               u.id as userid, u.name,
               COALESCE(CONCAT('[', c.tag, '] ', u.name), u.name) AS display_name
        FROM custom_scores cs
        INNER JOIN users u ON cs.user_id = u.id
        LEFT JOIN clans c ON c.id = u.clan_id
        WHERE {where_clause}
        ORDER BY cs.score DESC
        LIMIT :limit
    """,
    )

    results = await app.state.services.database.fetch_all(query, params)
    return [dict(result) for result in results]


async def get_personal_best_score(
    map_md5: str,
    user_id: int,
    mode: int,
    scoring_metric: str = "score",
) -> dict | None:
    """获取用户在自定义谱面上的个人最佳成绩"""

    query = text(
        f"""
        SELECT cs.id, cs.{scoring_metric} AS _score,
               cs.max_combo, cs.n50, cs.n100, cs.n300,
               cs.nmiss, cs.nkatu, cs.ngeki, cs.perfect, cs.mods,
               UNIX_TIMESTAMP(CONVERT_TZ(cs.play_time, @@session.time_zone, '+00:00')) as time, cs.pp, cs.acc
        FROM custom_scores cs
        WHERE cs.map_md5 = :map_md5
        AND cs.user_id = :user_id
        AND cs.mode = :mode
        AND cs.status = 2
        ORDER BY cs.{scoring_metric} DESC
        LIMIT 1
    """,
    )

    result = await app.state.services.database.fetch_one(
        query,
        {"map_md5": map_md5, "user_id": user_id, "mode": mode},
    )

    return dict(result) if result else None
