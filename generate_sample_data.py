"""Gera dados FICTÍCIOS de contadores horários de células 4G/5G.

Nenhum dado real de operadora é usado. Os valores são sintéticos, mas seguem
ordens de grandeza plausíveis para facilitar a demonstração do relatório.

Uso:
    python generate_sample_data.py --days 7 --sites 20 --out data/kpi_hourly.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

SECTORS = ["A", "B", "C"]
TECHS = {"LTE": 0.6, "NR": 0.4}  # proporção de células por tecnologia
CITIES = ["Rio de Janeiro", "Niterói", "Duque de Caxias", "Nova Iguaçu"]


def build_cells(n_sites: int, rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    for s in range(1, n_sites + 1):
        site = f"RJ{s:04d}"
        city = rng.choice(CITIES)
        for sec in SECTORS:
            tech = rng.choice(list(TECHS), p=list(TECHS.values()))
            band = "n78" if tech == "NR" else rng.choice(["B3", "B7", "B28"])
            rows.append(
                {
                    "cell": f"{site}_{tech}_{band}_{sec}",
                    "site": site,
                    "city": city,
                    "tech": tech,
                    "band": band,
                    "azimuth": {"A": 0, "B": 120, "C": 240}[sec] + int(rng.integers(-20, 20)),
                    "tilt": int(rng.integers(2, 9)),
                    # ~12% das células recebem um "problema" para aparecer no ranking
                    "issue": rng.choice(
                        ["none", "drops", "handover", "throughput"],
                        p=[0.88, 0.04, 0.04, 0.04],
                    ),
                }
            )
    return pd.DataFrame(rows)


def hourly_profile(hours: np.ndarray) -> np.ndarray:
    """Curva de tráfego diária (pico à noite)."""
    return 0.25 + 0.75 * np.exp(-((hours - 20) ** 2) / 18) + 0.35 * np.exp(-((hours - 12) ** 2) / 10)


def generate(days: int, n_sites: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    cells = build_cells(n_sites, rng)
    timestamps = pd.date_range("2026-10-01", periods=days * 24, freq="h")
    hours = timestamps.hour.to_numpy()
    profile = hourly_profile(hours)

    frames = []
    for c in cells.itertuples(index=False):
        n = len(timestamps)
        base_users = 120 if c.tech == "NR" else 200
        load = profile * base_users * rng.uniform(0.6, 1.4)

        rrc_att = rng.poisson(load * 40)
        rrc_succ = rng.binomial(rrc_att, rng.uniform(0.992, 0.999))

        erab_rel = rng.poisson(load * 35)
        drop_rate = 0.004 if c.tech == "LTE" else 0.006
        if c.issue == "drops":
            drop_rate *= 5
        erab_drop = rng.binomial(erab_rel, np.clip(rng.normal(drop_rate, drop_rate / 4, n), 0, 1))

        ho_att = rng.poisson(load * 12)
        ho_sr = 0.985 if c.issue != "handover" else 0.90
        ho_succ = rng.binomial(ho_att, np.clip(rng.normal(ho_sr, 0.005, n), 0, 1))

        # throughput médio de usuário (Mbps) cai com a carga
        thp_base = 180 if c.tech == "NR" else 35
        if c.issue == "throughput":
            thp_base *= 0.35
        thp = np.clip(thp_base * (1.15 - 0.5 * profile) * rng.normal(1, 0.08, n), 1, None)
        active_time_s = np.maximum(load * 900, 1)
        dl_volume_mbit = thp * active_time_s

        frames.append(
            pd.DataFrame(
                {
                    "timestamp": timestamps,
                    "cell": c.cell,
                    "rrc_conn_att": rrc_att,
                    "rrc_conn_succ": rrc_succ,
                    "erab_release_total": erab_rel,
                    "erab_abnormal_release": erab_drop,
                    "ho_att": ho_att,
                    "ho_succ": ho_succ,
                    "dl_volume_mbit": dl_volume_mbit.round(1),
                    "dl_active_time_s": active_time_s.round(1),
                }
            )
        )

    counters = pd.concat(frames, ignore_index=True)
    return counters.merge(cells.drop(columns="issue"), on="cell")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--days", type=int, default=7)
    p.add_argument("--sites", type=int, default=20)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--out", type=Path, default=Path("data/kpi_hourly.csv"))
    args = p.parse_args()

    df = generate(args.days, args.sites, args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)
    print(f"{len(df):,} linhas geradas em {args.out} ({df['cell'].nunique()} células)")


if __name__ == "__main__":
    main()
