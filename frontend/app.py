import os
import math
from typing import Any, Dict, List

import requests
import pandas as pd
import streamlit as st
import plotly.express as px

API_BASE = os.getenv("API_BASE", "http://localhost:8000")

st.set_page_config(page_title="ProyectoFutbol", layout="wide")
st.title("ProyectoFutbol — Buscador y análisis")


@st.cache_data(ttl=30)
def get_json(path: str, params=None) -> Dict[str, Any]:
    r = requests.get(f"{API_BASE}{path}", params=params, timeout=20)
    r.raise_for_status()
    return r.json()


def fix_rank_df(df: pd.DataFrame) -> pd.DataFrame:
    """Asegura que Valor es numérico, ordena y añade Rank."""
    if df.empty:
        return df
    out = df.copy()
    out["Valor"] = pd.to_numeric(out["Valor"], errors="coerce").fillna(0.0)
    # orden estable: valor desc y nombre asc
    out = out.sort_values(["Valor", "Jugador"], ascending=[False, True]).reset_index(drop=True)
    out["Rank"] = range(1, len(out) + 1)
    return out


def render_rank_bar(title: str, endpoint: str, params_base: Dict[str, Any], limit: int = 10) -> None:
    """Renderiza un barplot de ranking (Top N) de forma robusta."""
    res = get_json(endpoint, params={**params_base, "limit": int(limit)})
    items = res.get("items", []) or []

    df = pd.DataFrame([{
        "Jugador": it.get("player"),
        "Valor": it.get("value", 0),
        "Pos": it.get("pos"),
        "Equipo": (it.get("team_info") or {}).get("squad"),
    } for it in items])

    df = fix_rank_df(df)

    if df.empty:
        st.info(f"Sin datos para: {title}")
        return

    fig = px.bar(
        df,
        x="Jugador",
        y="Valor",
        color="Pos",
        hover_data=["Rank", "Equipo"],
        title=title,
    )
    fig.update_layout(xaxis={"categoryorder": "total descending", "tickangle": -45})
    st.plotly_chart(fig, use_container_width=True)


# ========= Sidebar filtros =========
st.sidebar.header("Filtros")

temporadas = (get_json("/options/temporadas").get("temporada") or [])
if not temporadas:
    st.error("No hay temporadas disponibles desde la API (/options/temporadas).")
    st.stop()

temporada = st.sidebar.selectbox("Temporada", temporadas, index=0)

comps = (get_json("/options/comp", params={"temporada": temporada}).get("comp") or [])
if not comps:
    st.error("No hay competiciones disponibles para esta temporada (/options/comp).")
    st.stop()

comp = st.sidebar.selectbox("Competición", comps, index=0)

pos = st.sidebar.selectbox("Posición", ["(Todas)", "GK", "DF", "MF", "FW"], index=0)
min_minutes = st.sidebar.number_input("Minutos mínimos", min_value=0, value=900, step=50)

limit = st.sidebar.slider("Resultados por página", 10, 100, 25, 5)
page = st.sidebar.number_input("Página", min_value=1, value=1, step=1)
skip = (page - 1) * limit

params_base: Dict[str, Any] = {"temporada": temporada, "comp": comp, "min": int(min_minutes)}
if pos != "(Todas)":
    params_base["pos"] = pos

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Jugadores", "Rankings", "Gráficos", "Top comunes", "Jugador"])


# ========= TAB 1: Jugadores =========
with tab1:
    st.subheader("Listado de jugadores")

    total = None
    try:
        cnt = get_json("/players/count", params=params_base)
        total = cnt.get("count")
        if total is not None:
            st.caption(f"Coincidencias: {total}")
    except Exception:
        st.caption("Coincidencias: (endpoint /players/count no disponible)")

    data = get_json("/players", params={**params_base, "limit": int(limit), "skip": int(skip)})
    items = data.get("items", []) or []

    rows: List[Dict[str, Any]] = []
    for it in items:
        rows.append({
            "Jugador": it.get("player"),
            "Pos": it.get("pos"),
            "Edad": it.get("age"),
            "Rango edad": it.get("rango_edad"),
            "Nación": it.get("nation"),
            "Equipo": (it.get("team_info") or {}).get("squad"),
            "Min": (it.get("stats_base") or {}).get("min"),
            "Goles": (it.get("stats_ataque") or {}).get("gls"),
            "Asist": (it.get("stats_ataque") or {}).get("ast"),
            "G+A": (it.get("stats_ataque") or {}).get("g_a"),
            "xG": (it.get("stats_avanzadas") or {}).get("xg"),
            "xAG": (it.get("stats_avanzadas") or {}).get("xag"),
        })

    df = pd.DataFrame(rows)
    if df.empty:
        st.warning("No hay resultados con esos filtros. Prueba a bajar minutos o quitar posición.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)

    if total is not None:
        pages = max(1, math.ceil(total / limit))
        st.caption(f"Página {page} de {pages} (skip={skip}, limit={limit})")


# ========= TAB 2: Rankings =========
with tab2:
    st.subheader("Rankings (Top 10)")

    col1, col2 = st.columns(2)

    with col1:
        render_rank_bar("Top Goles", "/rankings/goles", params_base, limit=10)
        render_rank_bar("Top xG", "/rankings/xg", params_base, limit=10)

    with col2:
        render_rank_bar("Top Asistencias", "/rankings/asistencias", params_base, limit=10)
        render_rank_bar("Top Goles + Asistencias", "/rankings/goles-asistencias", params_base, limit=10)


# ========= TAB 3: Gráficos =========
with tab3:
    st.subheader("Gráficos y comparativas")

    metric = st.selectbox(
        "Métrica para Top 10",
        options=[
            ("Goles", "/rankings/goles"),
            ("Asistencias", "/rankings/asistencias"),
            ("Goles+Asist", "/rankings/goles-asistencias"),
            ("xG", "/rankings/xg"),
        ],
        format_func=lambda x: x[0],
        key="metric_top10",
    )

    # ---- Top 10 barras (desde rankings) ----
    render_rank_bar(f"Top 10 — {metric[0]}", metric[1], params_base, limit=10)

    st.divider()

    # Para que los gráficos no se queden vacíos por min=900, usamos un min específico
    min_graph = st.slider(
        "Minutos mínimos (solo para gráficos)",
        0, 3000,
        min(int(min_minutes), 900),
        50,
        key="min_graph",
    )

    # Traemos una muestra de jugadores para scatter/pos (rápido)
    data2 = get_json("/players", params={**params_base, "min": int(min_graph), "limit": 200, "skip": 0})
    items2 = data2.get("items", []) or []

    df2 = pd.DataFrame([{
        "Jugador": it.get("player"),
        "Pos": it.get("pos"),
        "Rango edad": it.get("rango_edad"),
        "Equipo": (it.get("team_info") or {}).get("squad"),
        "Min": (it.get("stats_base") or {}).get("min"),
        "Goles": (it.get("stats_ataque") or {}).get("gls", 0),
        "Asist": (it.get("stats_ataque") or {}).get("ast", 0),
        "xG": (it.get("stats_avanzadas") or {}).get("xg", 0.0),
    } for it in items2])

    if df2.empty:
        st.info("No hay jugadores en la muestra para gráficos. Baja minutos o quita filtros.")
    else:
        colA, colB = st.columns(2)

        with colA:
            st.markdown("### Distribución por posición (muestra)")
            df_pos = df2.groupby("Pos", as_index=False).size().rename(columns={"size": "Jugadores"})
            fig = px.bar(df_pos, x="Pos", y="Jugadores", title="Jugadores por Posición")
            st.plotly_chart(fig, use_container_width=True)

        with colB:
            st.markdown("### Distribución por rangos de edad (TOTAL)")
            age = get_json("/analytics/age_ranges", params={**params_base, "min": int(min_graph)})
            df_age = pd.DataFrame(age.get("items", []) or [])

            if df_age.empty:
                st.info("Sin datos de rangos de edad con estos filtros.")
            else:
                fig = px.bar(df_age, x="rango_edad", y="count", title="Jugadores por rango de edad")
                fig.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Goles vs xG (scatter)")

    if df2.empty:
        st.info("No hay datos para el scatter con estos filtros.")
    else:
        df2 = df2.copy()
        df2["xG"] = pd.to_numeric(df2["xG"], errors="coerce").fillna(0.0)
        df2["Goles"] = pd.to_numeric(df2["Goles"], errors="coerce").fillna(0.0)
        df2["Min"] = pd.to_numeric(df2["Min"], errors="coerce").fillna(0.0)

        if df2["xG"].max() == 0:
            st.info("En esta temporada/dataset no hay xG (todos los valores son 0). Mostrando Goles vs Minutos.")
            fig = px.scatter(
                df2,
                x="Min",
                y="Goles",
                color="Pos",
                hover_name="Jugador",
                hover_data=["Equipo", "Rango edad"],
                title="Goles vs Minutos",
            )
        else:
            fig = px.scatter(
                df2,
                x="xG",
                y="Goles",
                color="Pos",
                hover_name="Jugador",
                hover_data=["Equipo", "Min", "Rango edad"],
                title="Goles vs xG",
            )

        fig.update_xaxes(rangemode="tozero")
        fig.update_yaxes(rangemode="tozero")
        st.plotly_chart(fig, use_container_width=True)

    # ======= Comparación 2 ligas (por rangos de edad) =======
    st.divider()
    st.subheader("Comparar 2 competiciones por rangos de edad")

    comp_list = comps

    c1, c2 = st.columns(2)
    with c1:
        compA = st.selectbox("Competición A", comp_list, index=0, key="compA")
    with c2:
        default_idx = 1 if len(comp_list) > 1 else 0
        compB = st.selectbox("Competición B", comp_list, index=default_idx, key="compB")

    if compA == compB:
        st.warning("Elige dos competiciones distintas para comparar.")
    else:
        cmp_data = get_json(
            "/analytics/age_ranges_compare",
            params={
                "temporada": temporada,
                "comp1": compA,
                "comp2": compB,
                "min": int(min_graph),
                **({"pos": pos} if pos != "(Todas)" else {}),
            },
        )
        df_cmp = pd.DataFrame(cmp_data.get("items", []) or [])

        if df_cmp.empty:
            st.info("Sin datos para comparar con esos filtros.")
        else:
            fig = px.bar(
                df_cmp,
                x="rango_edad",
                y="count",
                color="comp",
                barmode="group",
                title=f"Rangos de edad — {compA} vs {compB} ({temporada})",
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)


# ========= TAB 4: Top comunes =========
with tab4:
    st.subheader("Top comunes: goleadores vs asistentes")

    colx, coly = st.columns(2)
    with colx:
        top_n_g = st.slider("Top N goleadores", 5, 50, 20, 5, key="top_n_g")
    with coly:
        top_n_a = st.slider("Top N asistentes", 5, 50, 20, 5, key="top_n_a")

    top_g = get_json("/rankings/goles", params={**params_base, "limit": int(top_n_g)})
    top_a = get_json("/rankings/asistencias", params={**params_base, "limit": int(top_n_a)})

    df_g = pd.DataFrame([{
        "Jugador": it.get("player"),
        "Equipo": (it.get("team_info") or {}).get("squad"),
        "Pos": it.get("pos"),
        "Min": (it.get("stats_base") or {}).get("min"),
        "Goles": it.get("value", 0),
    } for it in (top_g.get("items", []) or [])])

    df_a = pd.DataFrame([{
        "Jugador": it.get("player"),
        "Equipo": (it.get("team_info") or {}).get("squad"),
        "Pos": it.get("pos"),
        "Min": (it.get("stats_base") or {}).get("min"),
        "Asistencias": it.get("value", 0),
    } for it in (top_a.get("items", []) or [])])

    if not df_g.empty:
        df_g["Goles"] = pd.to_numeric(df_g["Goles"], errors="coerce").fillna(0.0)
        df_g["Min"] = pd.to_numeric(df_g["Min"], errors="coerce").fillna(0.0)
    if not df_a.empty:
        df_a["Asistencias"] = pd.to_numeric(df_a["Asistencias"], errors="coerce").fillna(0.0)
        df_a["Min"] = pd.to_numeric(df_a["Min"], errors="coerce").fillna(0.0)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### Top Goleadores")
        st.dataframe(df_g, use_container_width=True, hide_index=True) if not df_g.empty else st.info("Sin datos.")
    with c2:
        st.markdown("### Top Asistentes")
        st.dataframe(df_a, use_container_width=True, hide_index=True) if not df_a.empty else st.info("Sin datos.")

    st.divider()

    if df_g.empty or df_a.empty:
        st.info("No hay suficientes datos para calcular comunes.")
    else:
        df_common = df_g.merge(df_a[["Jugador", "Asistencias"]], on="Jugador", how="inner")

        st.markdown("### Jugadores comunes en ambos tops")
        st.caption(f"Comunes: {len(df_common)} jugador(es)")

        if df_common.empty:
            st.info("No hay jugadores que aparezcan en ambos tops con estos filtros.")
        else:
            df_common = df_common.sort_values(["Goles", "Asistencias"], ascending=False).reset_index(drop=True)
            st.dataframe(df_common, use_container_width=True, hide_index=True)

            st.markdown("### Comparación visual (solo tops)")

            df_scatter = df_g[["Jugador", "Equipo", "Pos", "Min", "Goles"]].merge(
                df_a[["Jugador", "Asistencias"]],
                on="Jugador",
                how="outer",
            )
            df_scatter["Goles"] = pd.to_numeric(df_scatter["Goles"], errors="coerce").fillna(0.0)
            df_scatter["Asistencias"] = pd.to_numeric(df_scatter["Asistencias"], errors="coerce").fillna(0.0)

            set_g = set(df_g["Jugador"].tolist())
            set_a = set(df_a["Jugador"].tolist())

            def grupo(j: str) -> str:
                in_g = j in set_g
                in_a = j in set_a
                if in_g and in_a:
                    return "Top ambos"
                if in_g:
                    return "Top goles"
                return "Top asistencias"

            df_scatter["Grupo"] = df_scatter["Jugador"].apply(grupo)

            fig = px.scatter(
                df_scatter,
                x="Asistencias",
                y="Goles",
                color="Grupo",
                hover_name="Jugador",
                hover_data=["Equipo", "Pos", "Min"],
                title="Top goles vs top asistencias",
            )
            fig.update_yaxes(rangemode="tozero")
            fig.update_xaxes(rangemode="tozero")
            st.plotly_chart(fig, use_container_width=True)


# ========= TAB 5: Jugador =========
with tab5:
    st.subheader("Jugador — búsqueda y ficha")
    st.caption("Busca un jugador dentro de la temporada y competición seleccionadas en el panel lateral.")

    q = st.text_input(
        "Buscar jugador (mínimo 2 letras)",
        placeholder="Ej: Salah, Haaland, Pedri...",
        key="player_q",
    ).strip()

    cclr1, _ = st.columns([1, 5])
    with cclr1:
        if st.button("Limpiar", use_container_width=True):
            st.session_state["player_q"] = ""
            q = ""

    if len(q) < 2:
        st.info("Escribe al menos 2 letras para ver sugerencias.")
    else:
        sug = get_json(
            "/players/search",
            params={**params_base, "min": int(min_minutes), "q": q, "limit": 20},
        )

        items = sug.get("items", []) or []
        if not items:
            st.warning("No hay coincidencias con esos filtros.")
        else:
            df_sug = pd.DataFrame([{
                "Jugador": it.get("player"),
                "Equipo": (it.get("team_info") or {}).get("squad"),
                "Pos": it.get("pos"),
                "Min": (it.get("stats_base") or {}).get("min", 0),
                "Goles": (it.get("stats_ataque") or {}).get("gls", 0),
                "Asist": (it.get("stats_ataque") or {}).get("ast", 0),
                "xG": (it.get("stats_avanzadas") or {}).get("xg", 0.0),
            } for it in items])

            for c in ["Min", "Goles", "Asist"]:
                df_sug[c] = pd.to_numeric(df_sug[c], errors="coerce").fillna(0).astype(int)
            df_sug["xG"] = pd.to_numeric(df_sug["xG"], errors="coerce").fillna(0.0)

            df_sug["label"] = (
                df_sug["Jugador"].fillna("") + " — " +
                df_sug["Equipo"].fillna("") + " (" +
                df_sug["Pos"].fillna("") + ")"
            )

            st.markdown("### Selecciona jugador")
            label_sel = st.selectbox("Resultados", df_sug["label"].tolist(), key="player_label_sel")

            row_sel = df_sug.loc[df_sug["label"] == label_sel].iloc[0]
            jugador_sel = row_sel["Jugador"]

            prof = get_json(
                "/players/profile",
                params={"temporada": temporada, "comp": comp, "player": jugador_sel},
            )

            prof_items = prof.get("items", []) or []
            if not prof_items:
                st.warning("No se encontró el perfil completo del jugador.")
            else:
                it = prof_items[0]

                equipo = (it.get("team_info") or {}).get("squad", "")
                pos_it = it.get("pos", "")
                edad = it.get("age", "")
                nac = it.get("nation", "")

                st.markdown(f"## {jugador_sel}")
                st.caption(f"{equipo} · {comp} · {temporada} · {pos_it} · {nac} · Edad: {edad}")

                base = it.get("stats_base") or {}
                atk = it.get("stats_ataque") or {}
                adv = it.get("stats_avanzadas") or {}

                min_j = int(base.get("min", 0) or 0)
                gls_j = int(atk.get("gls", 0) or 0)
                ast_j = int(atk.get("ast", 0) or 0)
                ga_j = int(atk.get("g_a", gls_j + ast_j) or (gls_j + ast_j))
                xg_j = float(adv.get("xg", 0.0) or 0.0)
                xag_j = float(adv.get("xag", 0.0) or 0.0)

                m1, m2, m3, m4, m5, m6 = st.columns(6)
                m1.metric("Min", f"{min_j}")
                m2.metric("Goles", f"{gls_j}")
                m3.metric("Asist", f"{ast_j}")
                m4.metric("G+A", f"{ga_j}")
                m5.metric("xG", f"{xg_j:.2f}")
                m6.metric("xAG", f"{xag_j:.2f}")

                if xg_j == 0.0 and temporada == "21/22":
                    st.info("Nota: en 21/22 este dataset no incluye xG real (sale 0).")

                st.divider()

                def dict_to_df(d: dict) -> pd.DataFrame:
                    d = d or {}
                    return pd.DataFrame({"Campo": list(d.keys()), "Valor": list(d.values())})

                colL, colR = st.columns(2)
                with colL:
                    st.markdown("### Base")
                    st.dataframe(dict_to_df(it.get("stats_base")), use_container_width=True, hide_index=True)
                    st.markdown("### Ataque")
                    st.dataframe(dict_to_df(it.get("stats_ataque")), use_container_width=True, hide_index=True)
                with colR:
                    st.markdown("### Avanzadas")
                    st.dataframe(dict_to_df(it.get("stats_avanzadas")), use_container_width=True, hide_index=True)
                    st.markdown("### Por 90")
                    st.dataframe(dict_to_df(it.get("stats_por_90")), use_container_width=True, hide_index=True)
                    st.markdown("### Disciplina")
                    st.dataframe(dict_to_df(it.get("stats_disciplina")), use_container_width=True, hide_index=True)

                st.divider()
                st.markdown("### Mini comparación (ficha)")
                df_mini = pd.DataFrame([{
                    "Métrica": "Goles",
                    "Valor": gls_j,
                }, {
                    "Métrica": "Asistencias",
                    "Valor": ast_j,
                }, {
                    "Métrica": "xG",
                    "Valor": xg_j,
                }, {
                    "Métrica": "xAG",
                    "Valor": xag_j,
                }])

                fig = px.bar(df_mini, x="Métrica", y="Valor", title="Resumen")
                fig.update_yaxes(rangemode="tozero")
                st.plotly_chart(fig, use_container_width=True)