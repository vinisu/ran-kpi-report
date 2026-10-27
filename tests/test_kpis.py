import pandas as pd

from kpi_report.kpis import aggregate, compute_kpis
from kpi_report.worst_cells import find_worst_cells


def _counters(**over):
    base = dict(
        rrc_conn_att=1000, rrc_conn_succ=995,
        erab_release_total=1000, erab_abnormal_release=5,
        ho_att=500, ho_succ=490,
        dl_volume_mbit=30000.0, dl_active_time_s=1000.0,
    )
    base.update(over)
    return base


def test_kpi_formulas():
    df = compute_kpis(pd.DataFrame([_counters()]))
    row = df.iloc[0]
    assert row.rrc_sr == 99.5
    assert row.dcr == 0.5
    assert row.ho_sr == 98.0
    assert row.dl_thp_mbps == 30.0


def test_zero_denominator_gives_nan():
    df = compute_kpis(pd.DataFrame([_counters(ho_att=0, ho_succ=0)]))
    assert pd.isna(df.iloc[0].ho_sr)


def test_aggregate_uses_counter_sum_not_mean_of_rates():
    # 1/10 drops e 0/990 drops: média dos % daria 5%, o correto é 0.1%
    df = pd.DataFrame([
        {"cell": "X", **_counters(erab_release_total=10, erab_abnormal_release=1)},
        {"cell": "X", **_counters(erab_release_total=990, erab_abnormal_release=0)},
    ])
    agg = aggregate(df, ["cell"])
    assert round(agg.iloc[0].dcr, 3) == 0.1


def test_worst_cells_respects_min_volume():
    cells = compute_kpis(pd.DataFrame([
        {"cell": "BAD", "site": "S1", "city": "Rio", "tech": "LTE", "band": "B3", "azimuth": 0, "tilt": 4,
         **_counters(erab_abnormal_release=50)},
        {"cell": "LOW_TRAFFIC", "site": "S2", "city": "Rio", "tech": "LTE", "band": "B3", "azimuth": 0, "tilt": 4,
         **_counters(erab_release_total=50, erab_abnormal_release=10)},
    ]))
    worst = find_worst_cells(cells)
    dcr_cells = set(worst.loc[worst.kpi == "dcr", "cell"])
    assert dcr_cells == {"BAD"}
