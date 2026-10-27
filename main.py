"""Pipeline: CSV de contadores -> KPIs -> worst cells -> Excel + PowerPoint.

Uso:
    python main.py --input data/kpi_hourly.csv --out output
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from kpi_report.excel_report import build_excel
from kpi_report.kpis import aggregate
from kpi_report.pptx_report import build_pptx
from kpi_report.worst_cells import add_suggestions, find_worst_cells

CELL_ATTRS = ["cell", "site", "city", "tech", "band", "azimuth", "tilt"]


def run(input_csv: Path, out_dir: Path) -> dict[str, Path]:
    df = pd.read_csv(input_csv, parse_dates=["timestamp"])
    df["date"] = df["timestamp"].dt.normalize()

    network_daily = aggregate(df, ["date", "tech"])
    cell_kpis = aggregate(df, CELL_ATTRS)
    worst = add_suggestions(find_worst_cells(cell_kpis))

    excel = build_excel(network_daily, cell_kpis, worst, out_dir / "relatorio_kpis.xlsx")
    pptx = build_pptx(network_daily, worst, out_dir / "relatorio_kpis.pptx", out_dir / "charts")
    worst.to_csv(out_dir / "worst_cells.csv", index=False)

    print(f"Células analisadas: {cell_kpis['cell'].nunique()}")
    print(f"Ocorrências de worst cell: {len(worst)}")
    print(worst.head(5)[["cell", "kpi", "value", "threshold", "priority_score"]].to_string(index=False))
    return {"excel": excel, "pptx": pptx}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--input", type=Path, default=Path("data/kpi_hourly.csv"))
    p.add_argument("--out", type=Path, default=Path("output"))
    args = p.parse_args()
    outputs = run(args.input, args.out)
    for name, path in outputs.items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
