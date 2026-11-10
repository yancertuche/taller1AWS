#!/usr/bin/env python3
"""Verifica HTTP real (incluido EC2) y guarda un informe sin credenciales."""

import argparse
from datetime import datetime
import json
from pathlib import Path
import sys
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import urlopen
from zoneinfo import ZoneInfo


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="Ejemplo: http://127.0.0.1:5000")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--fixture", action="store_true", help="Exige la media artificial 115.0")
    args = parser.parse_args()
    parts = urlsplit(args.url)
    if parts.scheme not in ("http", "https") or not parts.hostname or parts.username or parts.password or parts.query or parts.fragment or parts.path not in ("", "/"):
        parser.error("Usa una URL HTTP(S) de origen, sin credenciales, rutas ni parámetros.")
    base = args.url.rstrip("/")
    checks = []

    def check(path, expected, validate):
        try:
            try:
                response = urlopen(base + path, timeout=50)
            except HTTPError as error:
                response = error
            with response:
                status, body = response.status, response.read().decode("utf-8")
            result = {"path": path, "status": status, "expected": expected,
                      "ok": status == expected}
            if result["ok"]:
                validate(body)
            elif body:
                try:
                    result["response"] = json.loads(body)
                except json.JSONDecodeError:
                    result["response"] = body[:300]
        except Exception as error:
            result = {"path": path, "ok": False, "error": str(error)}
        checks.append(result)
        print(json.dumps(result, ensure_ascii=False))

    def health(body):
        if json.loads(body).get("status") != "ok":
            raise ValueError("La salud no es ok")

    def error(body):
        if json.loads(body)["error"]["code"] != "invalid_date":
            raise ValueError("Código de validación inesperado")

    def stock(body):
        data = json.loads(body)
        if data["ticker"] != "GOOGL" or data["count"] < 1 or len(data["prices"]) != data["count"]:
            raise ValueError("Respuesta bursátil incompleta")
        closes = [row["Close"] for row in data["prices"]]
        if abs(data["mean_close"] - sum(closes) / len(closes)) > 1e-6:
            raise ValueError("Promedio incorrecto")
        if args.fixture and (data["mean_close"] != 115.0 or data["count"] != 3):
            raise ValueError("La respuesta no coincide con el fixture")
        checks.append({"market_data": "artificial" if args.fixture else "Yahoo Finance real",
                       "ticker": data["ticker"], "count": data["count"],
                       "mean_close": data["mean_close"], "ok": True})

    def html(body):
        if "<table" not in body or "GOOGL" not in body:
            raise ValueError("No se recibió la tabla HTML")

    params = "ticker=GOOGL&start=2024-01-01&end=2024-02-01"
    check("/health", 200, health)
    check("/api/stock?start=bad", 400, error)
    check("/api/stock?" + params, 200, stock)
    check("/?" + params, 200, html)
    report = {"time": datetime.now(ZoneInfo("America/Bogota")).isoformat(),
              "url": base, "fixture": args.fixture, "checks": checks,
              "passed": all(item["ok"] for item in checks)}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
