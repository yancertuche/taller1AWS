"""Configuración compartida por Ubuntu local y el contenedor."""

bind = "0.0.0.0:5000"
workers = 2
worker_class = "sync"
timeout = 45
graceful_timeout = 30
accesslog = "-"
errorlog = "-"
capture_output = True
