"""Servicio HTTP del Taller 1; usar Gunicorn para el despliegue."""

from datetime import date

from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import HTTPException

import read_value_yf as stocks

app = Flask(__name__)
app.config.update(MAX_CONTENT_LENGTH=16384)


def query():
    allowed = {"ticker", "start", "end"}
    if set(request.args) - allowed or any(len(request.args.getlist(k)) != 1 for k in request.args):
        raise stocks.StockError("Usa únicamente ticker, start y end, sin repetir parámetros.",
                                "invalid_parameters", 400)
    return stocks.validate_query(
        request.args.get("start", stocks.DEFAULT_START),
        request.args.get("ticker", stocks.DEFAULT_STOCK),
        request.args.get("end"),
    )


@app.get("/health")
def health():
    # Liveness local; no hace peticiones al proveedor externo.
    return jsonify(status="ok", service="stock-market")


@app.get("/")
def index():
    start, ticker, end = query()
    data = stocks.get_stock_data(start, ticker, end)
    return render_template("index.html", ticker=ticker, start=start, end=end,
                           mean_close=f"{data['Close'].mean():.4f}", count=len(data),
                           table=data.tail(5).to_html(border=0, escape=True),
                           today=date.today().isoformat())


@app.get("/api/stock")
def stock():
    start, ticker, end = query()
    data = stocks.get_stock_data(start, ticker, end)
    return jsonify(stocks.stock_payload(data, start, ticker, end))


@app.errorhandler(stocks.StockError)
def stock_error(error):
    if error.status >= 500:
        app.logger.warning("Consulta bursátil fallida: %s", error.code)
    response = jsonify(error={"code": error.code, "message": str(error)})
    if error.code == "rate_limited":
        response.headers["Retry-After"] = "60"
    return response, error.status


@app.errorhandler(HTTPException)
def http_error(error):
    response = error.get_response()
    response.data = app.json.dumps({"error": {"code": f"http_{error.code}",
                                              "message": error.description}})
    response.content_type = "application/json"
    return response


@app.errorhandler(Exception)
def unexpected_error(error):
    app.logger.exception("Error interno del servicio")
    return jsonify(error={"code": "internal_error", "message": "Error interno del servicio."}), 500


@app.after_request
def response_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Cache-Control"] = "no-store"
    response.headers["Content-Security-Policy"] = "default-src 'none'; form-action 'self'; frame-ancestors 'none'"
    return response


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
