"""Cálculo de KPIs de rede de acesso rádio (RAN) a partir de contadores.

Fórmulas simplificadas, no estilo usado em relatórios de otimização:

- RRC Setup SR (%)   = rrc_conn_succ / rrc_conn_att * 100
- DCR (%)            = erab_abnormal_release / erab_release_total * 100
- HO SR (%)          = ho_succ / ho_att * 100
- DL User Thp (Mbps) = dl_volume_mbit / dl_active_time_s

Os KPIs são sempre calculados a partir da SOMA dos contadores no período
(e não pela média de percentuais), que é a forma correta de agregar.
"""

from __future__ import annotations

import pandas as pd

COUNTERS = [
    "rrc_conn_att",
    "rrc_conn_succ",
    "erab_release_total",
    "erab_abnormal_release",
    "ho_att",
    "ho_succ",
    "dl_volume_mbit",
    "dl_active_time_s",
]

KPI_COLUMNS = ["rrc_sr", "dcr", "ho_sr", "dl_thp_mbps"]

KPI_LABELS = {
    "rrc_sr": "RRC Setup SR (%)",
    "dcr": "DCR (%)",
    "ho_sr": "HO SR (%)",
    "dl_thp_mbps": "DL User Thp (Mbps)",
}


def _safe_ratio(num: pd.Series, den: pd.Series, scale: float = 1.0) -> pd.Series:
    return (num / den.where(den > 0)) * scale


def compute_kpis(counters: pd.DataFrame) -> pd.DataFrame:
    """Adiciona colunas de KPI a um DataFrame que já contém os contadores."""
    out = counters.copy()
    out["rrc_sr"] = _safe_ratio(out["rrc_conn_succ"], out["rrc_conn_att"], 100)
    out["dcr"] = _safe_ratio(out["erab_abnormal_release"], out["erab_release_total"], 100)
    out["ho_sr"] = _safe_ratio(out["ho_succ"], out["ho_att"], 100)
    out["dl_thp_mbps"] = _safe_ratio(out["dl_volume_mbit"], out["dl_active_time_s"])
    return out


def aggregate(df: pd.DataFrame, by: list[str]) -> pd.DataFrame:
    """Soma os contadores pelo agrupamento pedido e recalcula os KPIs."""
    summed = df.groupby(by, as_index=False)[COUNTERS].sum()
    return compute_kpis(summed)
