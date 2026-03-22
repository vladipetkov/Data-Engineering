from typing import List, Tuple
from dataclasses import dataclass
import pandas as pd
from artist_cost import calculate_artist_cost
from appeal_model import build_appeal_scores
from genre_mapper import map_broad_genres
from stage import Stage
from pulp import (
    LpBinary,
    LpMaximize,
    LpMinimize,
    LpProblem,
    LpStatus,
    LpVariable,
    PULP_CBC_CMD,
    lpSum,
    value)


@dataclass
class FestivalInputs:
    database_path: str
    n_days: int
    performances_per_day_per_stage: int
    stages: List[Stage]
    total_budget: float
    hit_percentile: float
    objective: str = "max_appeal"


def _build_master_artist_table(database_path: str, hit_percentile: float):
# Builds one main artist table with cost, appeal, and broad genres
    cost_df = calculate_artist_cost(database_path)[["id", "cost_of_artist"]]
    appeal_df = build_appeal_scores(database_path,hit_percentile=hit_percentile)[["id", "name", "appeal_score"]]

    genre_df = map_broad_genres(database_path)[["id", "name", "broad_genres"]]
    df = appeal_df.merge(cost_df, on="id", how="left")
    df = df.merge(genre_df, on=["id", "name"], how="left")

    df["cost_of_artist"] = pd.to_numeric(df["cost_of_artist"]).fillna(0.0)
    df["appeal_score"] = pd.to_numeric(df["appeal_score"]).fillna(0.0)
    df["broad_genres"] = df["broad_genres"].apply(lambda x: x if isinstance(x, list) else [])

    return df


def _build_stage_eligibility_and_cost_tables(master: pd.DataFrame, stages: List[Stage]):
# Builds eligibility and stage-specific cost tables for every artist and stage
    df = master[["id", "name", "appeal_score", "cost_of_artist", "broad_genres"]].copy()
    stage_keys: List[str] = []
    for i, stage in enumerate(stages):
        key = f"stage_{i}"
        stage_keys.append(key)
        if stage.is_main_stage():
            allowed = df["broad_genres"].apply(lambda gs: 1 if isinstance(gs, list) and len(gs) > 0 else 0).astype(int)
        else:
            allowed_set = set(stage.stage_genres or set())
            allowed = df["broad_genres"].apply(
                lambda gs: 1 if len(allowed_set.intersection(set(gs))) > 0 else 0
            ).astype(int)

        df[key] = allowed
        df[f"{key}_cost"] = df.apply(
            lambda row: float(row["cost_of_artist"]) if row[key] == 1 else 0.0,
            axis=1)
    return df, stage_keys


def _recompute_stage_totals(stage: Stage):
# Recomputes total stage cost and total stage appeal from assigned performers
    performers = getattr(stage, "performers", []) or []
    stage.total_cost = float(sum(float(p.get("cost_of_artist", 0.0)) for p in performers))
    stage.sum_appeal = float(sum(float(p.get("appeal_score", 0.0)) for p in performers))


def _stages_to_lineup_table(stages: List[Stage]):
# Converts the optimized stage assignments into a lineup table
    rows = []
    for stage in stages:
        for performer in getattr(stage, "performers", []):
            rows.append(
                {"stage": stage.name,
                 "artist_id": performer["id"],
                 "artist_name": performer["name"],
                 "appeal_score": performer["appeal_score"],
                 "cost_of_artist": performer["cost_of_artist"],
                 "broad_genres": performer["broad_genres"]})
    return pd.DataFrame(rows)


def _stages_to_budget_table(stages: List[Stage]):
# Converts the optimized stage assignments into a budget summary table
    rows = []
    for stage in stages:
        rows.append(
            {"stage": stage.name,
             "stage_budget": stage.max_budget,
             "total_cost": getattr(stage, "total_cost", 0.0),
             "remaining_budget": stage.max_budget - getattr(stage, "total_cost", 0.0),
             "total_appeal": getattr(stage, "sum_appeal", 0.0)})
    return pd.DataFrame(rows)


def optimize_festival_lineup(inputs: FestivalInputs):
# Runs the festival lineup optimization model

    master = _build_master_artist_table(inputs.database_path, inputs.hit_percentile)
    wide, stage_keys = _build_stage_eligibility_and_cost_tables(master, inputs.stages)
    slots_per_stage = inputs.n_days * inputs.performances_per_day_per_stage
    wide["id"] = wide["id"].astype(str)
    artist_ids = wide["id"].tolist()
    appeal = dict(zip(wide["id"], wide["appeal_score"]))
    allowed = {}
    cost = {}

    for key in stage_keys:
        for id, alw, cst in zip(wide["id"],wide[key],wide[f"{key}_cost"]):
            allowed[(id, key)] = int(alw)
            cost[(id, key)] = float(cst)

    if inputs.objective == "min_appeal":
        prob = LpProblem("Festival_Global_Assignment", LpMinimize)
    else:
        prob = LpProblem("Festival_Global_Assignment", LpMaximize)

    x = LpVariable.dicts(
        "x",
        ((id, key) for id in artist_ids for key in stage_keys),
        lowBound=0,
        upBound=1,
        cat=LpBinary)

    prob += lpSum(appeal[id] * x[(id, key)] for id in artist_ids for key in stage_keys)

    for id in artist_ids:
        for key in stage_keys:
            prob += x[(id, key)] <= allowed[(id, key)]
    for id in artist_ids:
        prob += lpSum(x[(id, key)] for key in stage_keys) <= 1
    for key in stage_keys:
        prob += lpSum(x[(id, key)] for id in artist_ids) == slots_per_stage
    for key, stage in zip(stage_keys, inputs.stages):
        prob += lpSum(cost[(id, key)] * x[(id, key)] for id in artist_ids) <= stage.max_budget

    prob += lpSum(cost[(id, key)] * x[(id, key)] for id in artist_ids for key in stage_keys) <= inputs.total_budget
    prob.solve(PULP_CBC_CMD(msg=False))

    status = LpStatus[prob.status]

    if status not in {"Optimal", "Feasible"}:
        return {
            "stages": inputs.stages,
            "master": master,
            "wide": wide,
            "lineup": pd.DataFrame(),
            "budget": pd.DataFrame(),
            "solver_status": status,
            "objective": inputs.objective}

    for stage in inputs.stages:
        stage.performers = []
        stage.total_cost = 0
        stage.sum_appeal = 0

    stage_map = {key: stage for key, stage in zip(stage_keys, inputs.stages)}
    info = wide.set_index("id")[["name", "appeal_score", "broad_genres"]]

    for id in artist_ids:
        for key in stage_keys:
            if value(x[(id, key)]) > 0.5:
                performer = {
                    "id": id,
                    "name": info.loc[id, "name"],
                    "appeal_score": float(info.loc[id, "appeal_score"]),
                    "cost_of_artist": cost[(id, key)],
                    "broad_genres": info.loc[id, "broad_genres"]}
                stage_map[key].performers.append(performer)

    for stage in inputs.stages:
        stage.performers.sort(key=lambda p: p["appeal_score"], reverse=True)
        _recompute_stage_totals(stage)

    lineup = _stages_to_lineup_table(inputs.stages)
    budget = _stages_to_budget_table(inputs.stages)

    return {
        "stages": inputs.stages,
        "master": master,
        "wide": wide,
        "lineup": lineup,
        "budget": budget,
        "solver_status": status,
        "objective": inputs.objective}