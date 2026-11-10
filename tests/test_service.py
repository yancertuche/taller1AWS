import contextlib
from datetime import date, timedelta
import io
import json
import unittest
from unittest.mock import patch

import pandas as pd
from curl_cffi.requests.exceptions import Timeout
from yfinance.exceptions import YFPricesMissingError, YFRateLimitError, YFTzMissingError

from app import app
import read_value_yf as stocks
from tests.fixtures import prices


class QueryTests(unittest.TestCase):
    def test_normalizes_ticker(self):
        self.assertEqual(stocks.validate_query("2024-01-01", " googl ", "2024-02-01"),
                         ("2024-01-01", "GOOGL", "2024-02-01"))

    def test_symbols(self):
        for ticker in ("^GSPC", "BRK-B", "BTC-USD", "GC=F", "0700.HK"):
            with self.subTest(ticker=ticker):
                self.assertEqual(stocks.validate_query("2024-01-01", ticker, "2024-02-01")[1], ticker)

    def test_invalid_input(self):
        for start, ticker, end in (
            ("2024-1-01", "GOOGL", "2024-02-01"),
            ("2024-02-30", "GOOGL", "2024-03-01"),
            ("2024-02-01", "GOOGL", "2024-01-01"),
            ("2024-01-01", "GOOGL", "2024-01-01"),
            ("2024-01-01", "", "2024-02-01"),
            ("2024-01-01", "<script>", "2024-02-01"),
            ("2024-01-01", "AAPL MSFT", "2024-02-01"),
            ("2024-01-01", "A" * 25, "2024-02-01"),
            ("2024-01-01", None, "2024-02-01"),
            ("2000-01-01", "GOOGL", "2024-02-01"),
            ("2024-01-01", "GOOGL", (date.today() + timedelta(days=2)).isoformat()),
        ):
            with self.subTest(start=start, ticker=ticker, end=end):
                with self.assertRaises(stocks.StockError) as caught:
                    stocks.validate_query(start, ticker, end)
                self.assertEqual(caught.exception.status, 400)

    def test_dynamic_default_end(self):
        class FrozenDate(date):
            @classmethod
            def today(cls):
                return cls(2025, 1, 15)

        with patch.object(stocks, "date", FrozenDate):
            self.assertEqual(stocks.validate_query()[2], "2025-01-15")


class DataTests(unittest.TestCase):
    def setUp(self):
        self.patcher = patch.object(stocks.yf, "Ticker")
        self.ticker = self.patcher.start()
        self.addCleanup(self.patcher.stop)
        self.ticker.return_value.history.return_value = prices()

    def get(self):
        return stocks.get_stock_data("2024-01-01", "GOOGL", "2024-02-01")

    def test_download_parameters(self):
        data = self.get()
        self.ticker.assert_called_once_with("GOOGL")
        self.ticker.return_value.history.assert_called_once_with(
            start="2024-01-01", end="2024-02-01", interval="1d", auto_adjust=False,
            actions=False, timeout=10, raise_errors=True)
        self.assertEqual(data["Close"].mean(), 115.0)

    def test_invalid_query_never_calls_provider(self):
        with self.assertRaises(stocks.StockError):
            stocks.get_stock_data("bad", "GOOGL")
        self.ticker.assert_not_called()

    def test_empty_data(self):
        for data in (None, pd.DataFrame()):
            self.ticker.return_value.history.return_value = data
            with self.assertRaises(stocks.StockError) as caught:
                self.get()
            self.assertEqual(caught.exception.status, 404)

    def test_missing_columns(self):
        self.ticker.return_value.history.return_value = prices().drop(columns="Close")
        with self.assertRaises(stocks.StockError) as caught:
            self.get()
        self.assertEqual(caught.exception.status, 502)

    def test_filters_invalid_closes(self):
        data = prices()
        data["Close"] = [float("nan"), float("inf"), 125]
        self.ticker.return_value.history.return_value = data
        self.assertEqual(self.get()["Close"].tolist(), [125])

    def test_all_invalid_closes(self):
        data = prices()
        data["Close"] = float("nan")
        self.ticker.return_value.history.return_value = data
        with self.assertRaises(stocks.StockError) as caught:
            self.get()
        self.assertEqual(caught.exception.status, 404)

    def test_provider_errors(self):
        cases = (
            (YFRateLimitError(), 503, "rate_limited"),
            (YFPricesMissingError("GOOGL", "test"), 404, "no_data"),
            (YFTzMissingError("GOOGL"), 404, "no_data"),
            (Timeout("timeout"), 504, "provider_timeout"),
            (RuntimeError("secret-detail"), 502, "provider_error"),
        )
        for error, status, code in cases:
            with self.subTest(code=code):
                self.ticker.return_value.history.side_effect = error
                with self.assertRaises(stocks.StockError) as caught:
                    self.get()
                self.assertEqual((caught.exception.status, caught.exception.code), (status, code))
                self.assertNotIn("secret-detail", str(caught.exception))

    def test_json_has_null_and_dates(self):
        data = prices()
        data.loc[data.index[0], "Volume"] = float("nan")
        payload = stocks.stock_payload(data, "2024-01-01", "GOOGL", "2024-02-01")
        json.dumps(payload, allow_nan=False)
        self.assertIsNone(payload["prices"][0]["Volume"])
        self.assertEqual(payload["prices"][0]["date"], "2024-01-02")
        self.assertEqual(payload["mean_close"], 115.0)

    def test_cli(self):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            result = stocks.main(["AMZN", "--start", "2024-01-01", "--end", "2024-02-01"])
        self.assertEqual(result, 0)
        self.assertIn("115.0000", output.getvalue())

    def test_cli_error(self):
        with contextlib.redirect_stderr(io.StringIO()) as output:
            result = stocks.main(["<bad>"])
        self.assertEqual(result, 1)
        self.assertIn("invalid_ticker", output.getvalue())


class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.patcher = patch.object(stocks.yf, "Ticker")
        self.ticker = self.patcher.start()
        self.addCleanup(self.patcher.stop)
        self.ticker.return_value.history.return_value = prices()

    def test_health_does_not_need_yahoo(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["status"], "ok")
        self.ticker.assert_not_called()

    def test_html(self):
        response = self.client.get("/?ticker=AMZN&start=2024-01-01&end=2024-02-01")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.content_type)
        self.assertIn(b"AMZN", response.data)
        self.assertIn(b"115.0000", response.data)
        self.assertIn(b"<table", response.data)

    def test_api(self):
        response = self.client.get("/api/stock?ticker=googl&start=2024-01-01&end=2024-02-01")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["ticker"], "GOOGL")
        self.assertEqual(response.json["count"], 3)
        self.assertEqual(response.json["mean_close"], 115.0)
        self.assertTrue(response.json["end_exclusive"])

    def test_bad_requests(self):
        for path in ("/?ticker=%3Cscript%3E", "/api/stock?start=bad", "/api/stock?ticker=",
                     "/api/stock?ticker=AAPL&ticker=MSFT", "/?unknown=true", "/api/stock?end="):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 400)
        self.ticker.assert_not_called()

    def test_no_prices(self):
        self.ticker.return_value.history.return_value = pd.DataFrame()
        response = self.client.get("/api/stock")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json["error"]["code"], "no_data")

    def test_rate_limit(self):
        self.ticker.return_value.history.side_effect = YFRateLimitError()
        response = self.client.get("/api/stock")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.headers["Retry-After"], "60")

    def test_unavailable_provider(self):
        self.ticker.return_value.history.side_effect = RuntimeError("do-not-expose")
        response = self.client.get("/api/stock")
        self.assertEqual(response.status_code, 502)
        self.assertNotIn(b"do-not-expose", response.data)

    def test_http_errors(self):
        response = self.client.get("/missing")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json["error"]["code"], "http_404")
        response = self.client.post("/api/stock")
        self.assertEqual(response.status_code, 405)
        self.assertIn("GET", response.headers["Allow"])

    def test_internal_error(self):
        with patch.object(stocks, "stock_payload", side_effect=RuntimeError("secret")):
            response = self.client.get("/api/stock")
        self.assertEqual(response.status_code, 500)
        self.assertNotIn(b"secret", response.data)

    def test_headers(self):
        response = self.client.get("/health")
        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(response.headers["X-Frame-Options"], "DENY")


if __name__ == "__main__":
    unittest.main()
