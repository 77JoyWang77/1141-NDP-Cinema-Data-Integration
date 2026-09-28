from datetime import datetime
from typing import Dict, List, Optional


# ========================
# Rating normalize
# ========================

RATING_MAP_VIESHOW = {
    "general": "普遍級",
    "childview": "保護級",
    "bigchild": "輔12級",
    "teenager": "輔15級",
    "adult": "限制級",
    "needCheck": "未分級",
}


def normalize_rating(rating: Optional[str], source: str) -> Optional[str]:
    if not rating:
        return None
    if source == "vieshow":
        return RATING_MAP_VIESHOW.get(rating.lower(), rating)
    return rating


def normalize_release_date(date_str: Optional[str]) -> Optional[str]:
    if not date_str:
        return None
    return date_str.replace("/", "-")


# ========================
# Core merge logic
# ========================

def merge_movie(
    showtime_movie: Optional[Dict],
    vieshow_movie: Optional[Dict],
) -> Dict:
    """
    合併同一部電影的 showtime / vieshow movie json
    """
    src = showtime_movie or vieshow_movie
    if not src:
        raise ValueError("merge_movie called with no source")

    movie: Dict = {}

    # ===== movie entity (source-agnostic) =====
    movie["title_cn"] = src.get("title_cn")
    movie["title_en"] = src.get("title_en")

    movie["release_date"] = normalize_release_date(
        src.get("release_date")
    )
    movie["runtime_min"] = src.get("runtime_min")

    movie["rating"] = normalize_rating(
        src.get("rating"),
        "showtime" if showtime_movie else "vieshow"
    )

    # director: showtime=str, vieshow=list
    if showtime_movie:
        movie["director"] = showtime_movie.get("director")
    else:
        directors = vieshow_movie.get("director", [])
        movie["director"] = directors[0] if directors else None

    # synopsis: prefer showtime
    movie["synopsis"] = (
        (showtime_movie or {}).get("synopsis")
        or (vieshow_movie or {}).get("story")
    )

    # ===== merge list fields =====
    movie["genres"] = sorted(set(
        (showtime_movie or {}).get("genres", [])
        + (vieshow_movie or {}).get("genres", [])
    ))

    movie["actors"] = sorted(set(
        (showtime_movie or {}).get("actors", [])
        + (vieshow_movie or {}).get("actors", [])
    ))

    # ===== source glue =====
    movie["source_ids"] = {
        "showtime": showtime_movie.get("movie_id") if showtime_movie else None,
        "vieshow": vieshow_movie.get("movie_id") if vieshow_movie else None,
    }

    movie["sources"] = [
        k for k, v in movie["source_ids"].items() if v
    ]

    # ===== available_cinemas (只放秀泰，威秀之後補) =====
    movie["available_cinemas"] = (
        showtime_movie.get("available_cinemas", [])
        if showtime_movie else []
    )

    movie["updated_at"] = datetime.utcnow()

    return movie


# ========================
# Public loader
# ========================

async def load_movies(
    db,
    showtime_movies: List[Dict],
    vieshow_movies: List[Dict],
):
    """
    Upsert movies collection
    - 以 title_cn 對齊
    - 只寫 movies
    """

    # 用 title_cn 當 merge key（你目前的實務做法）
    showtime_map = {m["title_cn"]: m for m in showtime_movies}
    vieshow_map = {m["title_cn"]: m for m in vieshow_movies}

    all_titles = set(showtime_map.keys()) | set(vieshow_map.keys())

    for title in all_titles:
        movie_doc = merge_movie(
            showtime_map.get(title),
            vieshow_map.get(title),
        )

        await db.movies.update_one(
            {"title_cn": title},
            {"$set": movie_doc},
            upsert=True
        )
