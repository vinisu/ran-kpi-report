# RAN KPI Report: automação de relatórios de performance 4G/5G

Pipeline em Python que transforma contadores horários de células LTE/NR em:

- **KPIs agregados** (RRC Setup SR, DCR, HO SR e DL User Throughput), calculados pela soma dos contadores, nunca pela média de percentuais;
- **ranking de worst cells**, com limiares por tecnologia, volume mínimo de tráfego e score de prioridade;
- **relatório Excel** formatado (openpyxl), com gráficos de tendência, filtros e destaque condicional;
- **apresentação PowerPoint** executiva (python-pptx + matplotlib) com as tendências e o Top 10 de ofensoras.

> ⚠️ Todos os dados deste repositório são **fictícios**, gerados por `generate_sample_data.py`. Nenhum dado de operadora ou fabricante é usado.

O projeto reproduz, de forma simplificada, o tipo de rotina que automatizei no estágio em otimização de RF: consolidar KPIs, achar as células ofensoras e entregar o relatório pronto para a reunião.

## Como rodar

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python generate_sample_data.py --days 7 --sites 20   # gera data/kpi_hourly.csv
python main.py --input data/kpi_hourly.csv --out output
pytest -q
```

Saídas em `output/`: `relatorio_kpis.xlsx`, `relatorio_kpis.pptx` e `worst_cells.csv`.
Exemplos já gerados estão em [`examples/`](examples/).

## Estrutura

```
├── generate_sample_data.py   # dados sintéticos (60 células, 7 dias, por hora)
├── main.py                   # pipeline CSV -> KPIs -> worst cells -> Excel/PPTX
├── kpi_report/
│   ├── kpis.py               # fórmulas e agregação correta por contadores
│   ├── worst_cells.py        # limiares, volume mínimo, score e ação sugerida
│   ├── excel_report.py       # openpyxl: tabelas, gráficos, formatação condicional
│   └── pptx_report.py        # python-pptx + matplotlib
└── tests/test_kpis.py        # testes das fórmulas e regras
```

## Fórmulas

| KPI | Fórmula |
|---|---|
| RRC Setup SR (%) | `rrc_conn_succ / rrc_conn_att × 100` |
| DCR (%) | `erab_abnormal_release / erab_release_total × 100` |
| HO SR (%) | `ho_succ / ho_att × 100` |
| DL User Thp (Mbps) | `dl_volume_mbit / dl_active_time_s` |

**Score de prioridade** = desvio relativo do limiar (%) × (volume da célula ÷ mediana da tecnologia).
Assim, uma célula muito ruim e com muito tráfego sobe no ranking, e KPIs com unidades diferentes ficam comparáveis.

## Tecnologias

Python · pandas · NumPy · openpyxl · python-pptx · matplotlib · pytest

## Autor

**Vinícius Abílio**, Engenharia de Telecomunicações · [LinkedIn](https://linkedin.com/in/vinicius-abilio-3930b7)
