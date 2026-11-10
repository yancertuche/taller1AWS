"""Entrada WSGI exclusiva para probar transporte HTTP con datos artificiales.

No se incluye en la imagen de producción: se monta explícitamente durante la prueba.
"""
from unittest.mock import patch

from app import app
from tests.fixtures import prices

provider = patch("read_value_yf.yf.Ticker").start()
provider.return_value.history.return_value = prices()
