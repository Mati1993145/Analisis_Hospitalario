"""
07_ingesta_egresos_deis.py
==========================
Capa 2 del sub-estudio de salud mental: ingesta de la base oficial de
EGRESOS HOSPITALARIOS del DEIS / MINSAL (datos abiertos, diagnostico CIE-10).

A diferencia de REM20 (que mide camas/flujo, sin diagnostico), esta base trae
el DIAGNOSTICO PRINCIPAL (DIAG1) en CIE-10, lo que permite aislar las
hospitalizaciones por TRASTORNOS MENTALES (capitulo V, F00-F99) y estudiar si
aumento la PATOLOGIA, no solo la ocupacion de camas.

Limitacion conocida: la base es de granularidad ANUAL (columna ANO_EGRESO, no
fecha), por lo que la serie es anual (no mensual como REM20).

Estrategia (eficiente en disco): por cada anio descarga el ZIP (~8-22 MB),
abre el CSV por streaming (Latin-1, separador ';'), detecta columnas por NOMBRE
del header, cuenta el total de egresos (denominador/control) y vuelca solo las
filas de salud mental (DIAG1 que empieza con 'F') a un consolidado. Luego borra
el CSV grande (~300 MB) para no acumular ~7 GB.

Salidas:
  - data/processed/egresos_salud_mental_deis.csv  (filas F, todos los anios)
  - data/processed/serie_anual_salud_mental.csv    (agregado anual + control)
  - data/raw/egresos_deis/_log_ingesta.txt
"""

import csv
import io
import os
import sys
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen

# --- rutas ---------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]          # .../Analisis_Hospitalario
RAW = ROOT / "data" / "raw" / "egresos_deis"
PROC = ROOT / "data" / "processed"
RAW.mkdir(parents=True, exist_ok=True)
PROC.mkdir(parents=True, exist_ok=True)

OUT_FILAS = PROC / "egresos_salud_mental_deis.csv"
OUT_SERIE = PROC / "serie_anual_salud_mental.csv"
LOG = RAW / "_log_ingesta.txt"

ANIOS = list(range(2001, 2026))                     # 2001..2025
URL = "https://repositoriodeis.minsal.cl/DatosAbiertos/EGRESOS/EGRESOS_{}.zip"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"

# columnas que conservamos del registro de egreso (por NOMBRE de header)
COLS_DESEADAS = [
    "ANO_EGRESO", "DIAG1", "SEXO", "GRUPO_EDAD",
    "REGION_RESIDENCIA", "DIAS_ESTADA", "CONDICION_EGRESO",
]

# grupos diagnosticos del capitulo V (CIE-10) por decenas
GRUPOS = {
    "F0": "F00-F09 Organicos (demencia)",
    "F1": "F10-F19 Sustancias",
    "F2": "F20-F29 Esquizofrenia/psicoticos",
    "F3": "F30-F39 Afectivos (depresion/bipolar)",
    "F4": "F40-F48 Ansiedad/estres/neuroticos",
    "F5": "F50-F59 Sindromes comportamentales",
    "F6": "F60-F69 Personalidad",
    "F7": "F70-F79 Discapacidad intelectual",
    "F8": "F80-F89 Desarrollo",
    "F9": "F90-F99 Infancia/adolescencia y sin esp.",
}


def grupo_de(diag1: str) -> str:
    """Mapea un codigo DIAG1 (p.ej. 'F321') a su grupo por decena ('F3')."""
    d = diag1.strip().upper()
    if len(d) >= 2 and d[0] == "F" and d[1].isdigit():
        return "F" + d[1]
    return "F?"


def log(msg: str):
    line = msg.rstrip("\n")
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def descargar(anio: int) -> Path:
    dst = RAW / f"EGRESOS_{anio}.zip"
    if dst.exists() and dst.stat().st_size > 0:
        return dst
    url = URL.format(anio)
    req = Request(url, headers={"User-Agent": UA})
    with urlopen(req, timeout=180) as resp, open(dst, "wb") as out:
        while True:
            chunk = resp.read(1 << 20)
            if not chunk:
                break
            out.write(chunk)
    return dst


def procesar_anio(anio: int, escritor_filas) -> dict:
    """Devuelve el agregado del anio: total, sm y conteo por grupo."""
    zip_path = descargar(anio)
    with zipfile.ZipFile(zip_path) as zf:
        nombre_csv = next(n for n in zf.namelist() if n.lower().endswith(".csv"))
        with zf.open(nombre_csv) as raw:
            texto = io.TextIOWrapper(raw, encoding="latin-1", newline="")
            lector = csv.reader(texto, delimiter=";")
            header = next(lector)
            idx = {c: header.index(c) for c in COLS_DESEADAS if c in header}
            if "DIAG1" not in idx:
                raise RuntimeError(f"{anio}: no se encontro DIAG1 en {header[:14]}")
            i_diag = idx["DIAG1"]
            total = 0
            sm = 0
            por_grupo = {g: 0 for g in GRUPOS}
            for fila in lector:
                if not fila:
                    continue
                total += 1
                try:
                    diag = fila[i_diag]
                except IndexError:
                    continue
                if diag[:1].upper() == "F":
                    sm += 1
                    g = grupo_de(diag)
                    if g in por_grupo:
                        por_grupo[g] += 1
                    # volcar fila consolidada
                    rec = []
                    for c in COLS_DESEADAS:
                        rec.append(fila[idx[c]] if c in idx and idx[c] < len(fila) else "")
                    rec.append(diag[:3].upper())   # cat3
                    rec.append(g)                  # grupo
                    escritor_filas.writerow(rec)
    # borrar CSV grande si quedo extraido (no deberia, pero por si acaso)
    for f in RAW.glob(f"EGRE_DATOS_ABIERTOS_{anio}.csv"):
        try:
            f.unlink()
        except OSError:
            pass
    agg = {"ano": anio, "egresos_total": total, "egresos_sm": sm}
    agg.update({g: por_grupo[g] for g in GRUPOS})
    return agg


def main():
    LOG.write_text("", encoding="utf-8")
    log(f"=== Ingesta egresos DEIS {ANIOS[0]}-{ANIOS[-1]} ===")
    series = []
    with open(OUT_FILAS, "w", encoding="utf-8", newline="") as fh_filas:
        w = csv.writer(fh_filas, delimiter=";")
        w.writerow(COLS_DESEADAS + ["CAT3", "GRUPO"])
        for anio in ANIOS:
            try:
                agg = procesar_anio(anio, w)
                series.append(agg)
                tasa = (agg["egresos_sm"] / agg["egresos_total"] * 10000) if agg["egresos_total"] else 0
                log(f"{anio}: total={agg['egresos_total']:>9,}  "
                    f"salud_mental={agg['egresos_sm']:>7,}  "
                    f"tasa={tasa:6.1f}/10mil")
            except Exception as exc:  # noqa: BLE001
                log(f"{anio}: ERROR -> {exc}")

    # escribir serie anual
    campos = ["ano", "egresos_total", "egresos_sm", "tasa_sm_x10mil"] + list(GRUPOS)
    with open(OUT_SERIE, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=campos, delimiter=";")
        w.writeheader()
        for s in series:
            tasa = (s["egresos_sm"] / s["egresos_total"] * 10000) if s["egresos_total"] else 0
            row = {"ano": s["ano"], "egresos_total": s["egresos_total"],
                   "egresos_sm": s["egresos_sm"], "tasa_sm_x10mil": round(tasa, 3)}
            for g in GRUPOS:
                row[g] = s[g]
            w.writerow(row)

    log(f"\nOK. Serie anual -> {OUT_SERIE}")
    log(f"Filas salud mental -> {OUT_FILAS}")
    log("Leyenda grupos:")
    for g, desc in GRUPOS.items():
        log(f"  {g}: {desc}")


if __name__ == "__main__":
    sys.exit(main())
