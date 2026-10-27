"""Identificação de worst cells (células ofensoras).

Uma célula é ofensora em um KPI quando viola o limiar E tem volume mínimo
de amostras (para não poluir o ranking com células de pouco tráfego).
Score de prioridade = desvio relativo do limiar (%) x peso de tráfego,
onde o peso é o volume da célula dividido pela mediana da tecnologia.
Assim KPIs com unidades diferentes ficam comparáveis no mesmo ranking.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class Threshold:
    kpi: str
    limit: float
    higher_is_better: bool
    volume_col: str
    min_volume: int


# Limiares de exemplo (ajustáveis por tecnologia/operadora)
DEFAULT_THRESHOLDS = {
    "LTE": [
        Threshold("dcr", 1.0, False, "erab_release_total", 500),
        Threshold("ho_sr", 97.0, True, "ho_att", 200),
        Threshold("rrc_sr", 99.0, True, "rrc_conn_att", 500),
        Threshold("dl_thp_mbps", 12.0, True, "dl_active_time_s", 10_000),
    ],
    "NR": [
        Threshold("dcr", 1.2, False, "erab_release_total", 300),
        Threshold("ho_sr", 97.0, True, "ho_att", 150),
        Threshold("rrc_sr", 99.0, True, "rrc_conn_att", 300),
        Threshold("dl_thp_mbps", 60.0, True, "dl_active_time_s", 10_000),
    ],
}


def find_worst_cells(cell_kpis: pd.DataFrame, thresholds=DEFAULT_THRESHOLDS) -> pd.DataFrame:
    """Retorna uma linha por (célula, KPI violado), ordenada por prioridade."""
    rows = []
    for tech, rules in thresholds.items():
        sub = cell_kpis[cell_kpis["tech"] == tech]
        for t in rules:
            enough = sub[t.volume_col] >= t.min_volume
            bad = sub[t.kpi] < t.limit if t.higher_is_better else sub[t.kpi] > t.limit
            offenders = sub[enough & bad]
            median_volume = max(sub[t.volume_col].median(), 1)
            for r in offenders.itertuples(index=False):
                value = getattr(r, t.kpi)
                gap_pct = abs(value - t.limit) / t.limit * 100
                weight = getattr(r, t.volume_col) / median_volume
                rows.append(
                    {
                        "cell": r.cell,
                        "site": r.site,
                        "city": r.city,
                        "tech": tech,
                        "band": r.band,
                        "kpi": t.kpi,
                        "value": round(value, 2),
                        "threshold": t.limit,
                        "volume": int(getattr(r, t.volume_col)),
                        "azimuth": r.azimuth,
                        "tilt": r.tilt,
                        "priority_score": round(gap_pct * weight, 2),
                    }
                )
    cols = ["cell", "site", "city", "tech", "band", "kpi", "value", "threshold",
            "volume", "azimuth", "tilt", "priority_score"]
    result = pd.DataFrame(rows, columns=cols)
    return result.sort_values("priority_score", ascending=False).reset_index(drop=True)


SUGGESTIONS = {
    "dcr": "Checar cobertura/interferência (RSRP/SINR), alarmes de hardware e parâmetros de RLF.",
    "ho_sr": "Revisar relações de vizinhança, offsets de HO (A3/hysteresis) e colisão de PCI.",
    "rrc_sr": "Verificar congestionamento de recursos, alarmes e parâmetros de acesso.",
    "dl_thp_mbps": "Avaliar carga/PRB, qualidade (CQI/SINR) e ajuste de tilt/azimute.",
}


def add_suggestions(worst: pd.DataFrame) -> pd.DataFrame:
    out = worst.copy()
    out["suggested_action"] = out["kpi"].map(SUGGESTIONS)
    return out
