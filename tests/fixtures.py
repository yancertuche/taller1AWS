"""Datos artificiales exclusivamente para pruebas; nunca son cotizaciones reales."""

import pandas as pd


def prices():
    return pd.DataFrame({
        "Open": [100.0, 110.0, 120.0],
        "High": [110.0, 120.0, 130.0],
        "Low": [90.0, 100.0, 110.0],
        "Close": [105.0, 115.0, 125.0],
        "Volume": [1000, 2000, 3000],
    }, index=pd.date_range("2024-01-02", periods=3, name="Date"))
