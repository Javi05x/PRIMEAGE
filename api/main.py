import os
import re
from enum import Enum
from typing import Optional

from fastapi import FastAPI, Query
from pymongo import MongoClient

app = FastAPI(title="ProyectoFutbol API", version="0.5.0")

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGO_DB", "ProyectoFutbol")
COLLECTION = os.getenv("MONGO_COLLECTION", "Jugadores")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
jugadores = db[COLLECTION]


class PosEnum(str, Enum):
    GK = "GK"
    DF = "DF"
    MF = "MF"
    FW = "FW"


@app.get("/health")
def health():
    return {"status": "ok"}


# ---- OPTIONS (para no memorizar valores) ----
@app.get("/options/temporadas")
def options_temporadas():
    vals = jugadores.distinct("team_info.temporada")
    vals = sorted([v for v in vals if v is not None])
    return {"temporada": vals}


@app.get("/options/comp")
def options_comp(
    temporada: Optional[str] = Query(default=None, description="Filtra competiciones por temporada"),
):
    q = {}
    if temporada:
        q["team_info.temporada"] = temporada
    vals = jugadores.distinct("team_info.comp", q)
    vals = sorted([v for v in vals if v is not None])
    return {"comp": vals}


@app.get("/options/pos")
def options_pos():
    vals = jugadores.distinct("pos")
    vals = sorted([v for v in vals if v is not None])
    return {"pos": vals}


@app.get("/options/rango_edad")
def options_rango_edad():
    vals = jugadores.distinct("rango_edad")
    vals = sorted([v for v in vals if v is not None])
    return {"rango_edad": vals}


def _build_match(
    temporada: Optional[str],
    comp: Optional[str],
    pos: Optional[PosEnum],
    min_minutes: int,
):
    match = {"stats_base.min": {"$gte": min_minutes}}
    if temporada:
        match["team_info.temporada"] = temporada
    if comp:
        match["team_info.comp"] = comp
    if pos:
        match["pos"] = pos.value
    return match


@app.get("/players")
def list_players(
    temporada: Optional[str] = Query(default=None, description="Ver opciones en GET /options/temporadas"),
    comp: Optional[str] = Query(default=None, description="Ver opciones en GET /options/comp (puedes filtrar por temporada)"),
    pos: Optional[PosEnum] = Query(default=None, description="Ver opciones en GET /options/pos"),
    min: int = Query(default=900, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    skip: int = Query(default=0, ge=0),
):
    match = _build_match(temporada, comp, pos, min)

    cursor = (
        jugadores.find(
            match,
            {
                "_id": 0,
                "player": 1,
                "pos": 1,
                "age": 1,
                "rango_edad": 1,
                "nation": 1,
                "team_info": 1,
                "stats_base.min": 1,
                "stats_ataque.gls": 1,
                "stats_ataque.ast": 1,
                "stats_ataque.g_a": 1,
                "stats_avanzadas.xg": 1,
                "stats_avanzadas.npxg": 1,
                "stats_avanzadas.xag": 1,
            },
        )
        .sort("player", 1)
        .skip(skip)
        .limit(limit)
    )

    return {"items": list(cursor), "skip": skip, "limit": limit}


@app.get("/players/count")
def players_count(
    temporada: Optional[str] = Query(default=None),
    comp: Optional[str] = Query(default=None),
    pos: Optional[PosEnum] = Query(default=None),
    min: int = Query(default=900, ge=0),
):
    match = _build_match(temporada, comp, pos, min)
    return {"count": jugadores.count_documents(match), "match": match}


def _ranking(field: str, temporada: Optional[str], comp: Optional[str], min_minutes: int, limit: int):
    match = _build_match(temporada, comp, None, min_minutes)
    match[field] = {"$exists": True}

    pipeline = [
        {"$match": match},
        {
            "$project": {
                "_id": 0,
                "player": 1,
                "pos": 1,
                "team_info": 1,
                "stats_base": {"min": "$stats_base.min"},
                "value": {
                    "$convert": {
                        "input": {"$ifNull": ["$" + field, 0]},
                        "to": "double",
                        "onError": 0,
                        "onNull": 0,
                    }
                },
            }
        },
        {"$sort": {"value": -1, "player": 1}},
        {"$limit": limit},
    ]
    return list(jugadores.aggregate(pipeline))


@app.get("/rankings/goles")
def ranking_goles(
    temporada: Optional[str] = Query(default=None),
    comp: Optional[str] = Query(default=None),
    min: int = Query(default=900, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
):
    return {"field": "stats_ataque.gls", "items": _ranking("stats_ataque.gls", temporada, comp, min, limit)}


@app.get("/rankings/asistencias")
def ranking_asistencias(
    temporada: Optional[str] = Query(default=None),
    comp: Optional[str] = Query(default=None),
    min: int = Query(default=900, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
):
    return {"field": "stats_ataque.ast", "items": _ranking("stats_ataque.ast", temporada, comp, min, limit)}


@app.get("/rankings/goles-asistencias")
def ranking_goles_asistencias(
    temporada: Optional[str] = Query(default=None),
    comp: Optional[str] = Query(default=None),
    min: int = Query(default=900, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
):
    return {"field": "stats_ataque.g_a", "items": _ranking("stats_ataque.g_a", temporada, comp, min, limit)}


@app.get("/rankings/xg")
def ranking_xg(
    temporada: Optional[str] = Query(default=None),
    comp: Optional[str] = Query(default=None),
    min: int = Query(default=900, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
):
    return {"field": "stats_avanzadas.xg", "items": _ranking("stats_avanzadas.xg", temporada, comp, min, limit)}


@app.get("/players/search")
def search_players(
    temporada: Optional[str] = Query(default=None),
    comp: Optional[str] = Query(default=None),
    pos: Optional[PosEnum] = Query(default=None),
    min: int = Query(default=0, ge=0),
    q: str = Query(..., min_length=1, description="Texto a buscar en el nombre del jugador"),
    limit: int = Query(default=15, ge=1, le=50),
):
    """
    Devuelve sugerencias de jugadores que coinciden con 'q' (case-insensitive),
    aplicando filtros de temporada/competición/posición/minutos.
    """
    match = _build_match(temporada, comp, pos, min)

    # Regex case-insensitive, escapando input del usuario para evitar patrones raros
    match["player"] = {"$regex": re.escape(q), "$options": "i"}

    cursor = (
        jugadores.find(
            match,
            {
                "_id": 0,
                "player": 1,
                "pos": 1,
                "rango_edad": 1,
                "nation": 1,
                "team_info": 1,
                "stats_base.min": 1,
                "stats_ataque.gls": 1,
                "stats_ataque.ast": 1,
                "stats_ataque.g_a": 1,
                "stats_avanzadas.xg": 1,
                "stats_avanzadas.xag": 1,
            },
        )
        .sort("stats_ataque.gls", -1)
        .limit(limit)
    )

    return {"items": list(cursor), "limit": limit, "q": q}


@app.get("/players/profile")
def player_profile(
    temporada: str = Query(...),
    comp: str = Query(...),
    player: str = Query(..., description="Nombre exacto del jugador (tal y como viene en la BD)"),
):
    """
    Devuelve la ficha completa de un jugador en una temporada/competición.
    (Si hay duplicados por algún motivo, devuelve una lista.)
    """
    match = {
        "team_info.temporada": temporada,
        "team_info.comp": comp,
        "player": player,
    }

    cursor = jugadores.find(
        match,
        {
            "_id": 0,
            "player": 1,
            "nation": 1,
            "pos": 1,
            "age": 1,
            "born": 1,
            "rango_edad": 1,
            "team_info": 1,
            "stats_base": 1,
            "stats_ataque": 1,
            "stats_disciplina": 1,
            "stats_avanzadas": 1,
            "stats_por_90": 1,
        },
    )

    items = list(cursor)
    return {"items": items, "count": len(items)}


@app.get("/analytics/age_ranges")
def analytics_age_ranges(
    temporada: Optional[str] = Query(default=None),
    comp: Optional[str] = Query(default=None),
    pos: Optional[PosEnum] = Query(default=None),
    min: int = Query(default=0, ge=0),
):
    """
    Cuenta jugadores por rango_edad aplicando filtros.
    Ideal para gráficos de distribución de edades en el frontend.
    """
    match = _build_match(temporada, comp, pos, min)

    pipeline = [
        {"$match": match},
        {"$match": {"rango_edad": {"$ne": None}}},
        {"$group": {"_id": "$rango_edad", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}},
        {"$project": {"_id": 0, "rango_edad": "$_id", "count": 1}},
    ]
    return {"items": list(jugadores.aggregate(pipeline))}


@app.get("/analytics/age_ranges_compare")
def analytics_age_ranges_compare(
    temporada: str = Query(..., description="Temporada obligatoria para comparar ligas"),
    comp1: str = Query(..., description="Competición 1"),
    comp2: str = Query(..., description="Competición 2"),
    pos: Optional[PosEnum] = Query(default=None),
    min: int = Query(default=0, ge=0),
):
    """
    Devuelve counts de jugadores por rango_edad para dos competiciones,
    para poder comparar en el frontend.
    """
    match_base = _build_match(temporada, None, pos, min)

    pipeline = [
        {
            "$match": {
                **match_base,
                "team_info.comp": {"$in": [comp1, comp2]},
                "rango_edad": {"$ne": None},
            }
        },
        {
            "$group": {
                "_id": {"comp": "$team_info.comp", "rango_edad": "$rango_edad"},
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"_id.comp": 1, "_id.rango_edad": 1}},
        {"$project": {"_id": 0, "comp": "$_id.comp", "rango_edad": "$_id.rango_edad", "count": 1}},
    ]

    return {"items": list(jugadores.aggregate(pipeline))}