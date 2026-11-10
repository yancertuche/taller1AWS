"""Consulta diaria de una acción, reutilizable desde CLI y Flask."""

import argparse
from datetime import date, datetime, timedelta
import re
import sys

import pandas as pd
import yfinance as yf
from yfinance.exceptions import YFPricesMissingError, YFRateLimitError, YFTzMissingError
from curl_cffi.requests.exceptions import Timeout

DEFAULT_START = "2020-01-01"
DEFAULT_STOCK = "GOOGL"
MAX_RANGE_DAYS = 3660
SYMBOL = re.compile(r"[A-Z0-9^][A-Z0-9.^=\-]{0,23}", re.ASCII)


class StockError(Exception):
    """Error público y estable, sin detalles internos del proveedor."""

    def __init__(self, message, code="provider_error", status=502):
        super().__init__(message)
        self.code = code
        self.status = status


def validate_query(sd=DEFAULT_START, stock=DEFAULT_STOCK, ed=None):
    """Normaliza un ticker y fechas ISO; la fecha final es exclusiva."""
    if not isinstance(stock, str) or not SYMBOL.fullmatch(stock.strip().upper()):
        raise StockError("El ticker debe contener entre 1 y 24 caracteres bursátiles válidos.",
                         "invalid_ticker", 400)
    stock = stock.strip().upper()
    ed = date.today() if ed is None else ed

    def parse(value):
        if type(value) is date:
            return value
        if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            raise ValueError
        return datetime.strptime(value, "%Y-%m-%d").date()

    try:
        start, end = parse(sd), parse(ed)
    except ValueError:
        raise StockError("Usa fechas válidas con formato YYYY-MM-DD.", "invalid_date", 400) from None
    if start >= end:
        raise StockError("La fecha inicial debe ser anterior a la final.", "invalid_range", 400)
    if end > date.today() + timedelta(days=1):
        raise StockError("La fecha final no puede superar mañana (límite exclusivo).",
                         "invalid_range", 400)
    if (end - start).days > MAX_RANGE_DAYS:
        raise StockError("El intervalo máximo es de 3660 días.", "invalid_range", 400)
    return start.isoformat(), stock, end.isoformat()


def get_stock_data(sd, stock, ed=None):
    """Conserva la interfaz del profesor y devuelve un DataFrame OHLCV."""
    start, ticker, end = validate_query(sd, stock, ed)
    try:
        # history permite distinguir errores; download suele devolver una tabla vacía.
        data = yf.Ticker(ticker).history(
            start=start, end=end, interval="1d", auto_adjust=False,
            actions=False, timeout=10, raise_errors=True,
        )
    except YFRateLimitError:
        raise StockError("Yahoo Finance limitó temporalmente las consultas. Intenta más tarde.",
                         "rate_limited", 503) from None
    except (YFPricesMissingError, YFTzMissingError):
        raise StockError("No hay datos para ese ticker y período.", "no_data", 404) from None
    except Timeout:
        raise StockError("Yahoo Finance excedió el tiempo de espera.", "provider_timeout", 504) from None
    except Exception as exc:
        raise StockError("No fue posible consultar Yahoo Finance. Intenta más tarde.") from exc
    if data is None or data.empty:
        raise StockError("No hay datos para ese ticker y período.", "no_data", 404)
    columns = ["Open", "High", "Low", "Close", "Volume"]
    if not all(column in data.columns for column in columns):
        raise StockError("Yahoo Finance devolvió una respuesta incompleta.")
    data = data[columns].copy()
    for column in columns:
        data[column] = pd.to_numeric(data[column], errors="coerce")
    data = data.replace([float("inf"), float("-inf")], float("nan"))
    data = data.dropna(subset=["Close"]).sort_index()
    if data.empty:
        raise StockError("No hay precios de cierre válidos para ese período.", "no_data", 404)
    return data


def stock_payload(data, start, ticker, end):
    """Genera JSON estándar: los valores ausentes se representan como null."""
    import json

    records = json.loads(data.to_json(orient="records"))
    for timestamp, row in zip(data.index, records):
        row["date"] = timestamp.date().isoformat()
    return {
        "ticker": ticker, "start": start, "end": end, "end_exclusive": True,
        "source": "Yahoo Finance (yfinance)", "interval": "1d",
        "auto_adjust": False, "count": len(data),
        "mean_close": float(data["Close"].mean()), "prices": records,
    }


def test(ticker=DEFAULT_STOCK):
    """Función del ejemplo del profesor; consulta real, no prueba automatizada."""
    return get_stock_data(DEFAULT_START, ticker)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ticker", nargs="?", default=DEFAULT_STOCK)
    parser.add_argument("--start", default=DEFAULT_START)
    parser.add_argument("--end", default=None, help="Fecha final exclusiva YYYY-MM-DD")
    args = parser.parse_args(argv)
    try:
        start, ticker, end = validate_query(args.start, args.ticker, args.end)
        data = get_stock_data(start, ticker, end)
    except StockError as exc:
        print(f"Error [{exc.code}]: {exc}", file=sys.stderr)
        return 1
    print(f"Stock {ticker}: {start} <= fecha < {end}")
    print(data.tail())
    print(f"Promedio de cierre: {data['Close'].mean():.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
