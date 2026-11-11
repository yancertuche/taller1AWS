# Taller 1: servicio bursátil con Flask, Docker y AWS EC2

En este taller desarrollé un servicio en Python para consultar datos bursátiles de Yahoo Finance. Partí del ejemplo del profesor: ejecutar la consulta como un script, exponerla con Flask y empaquetarla en Docker para llevarla a una máquina virtual.

El servicio muestra los últimos cinco registros y calcula el promedio de cierre del período completo. Utilicé Gunicorn para atender las solicitudes HTTP.

- Código: [yancertuche/taller1AWS](https://github.com/yancertuche/taller1AWS).
- Imagen pública: [yancertuche/stock-market:1.0](https://hub.docker.com/r/yancertuche/stock-market).
- [Resultados y evidencias](docs/EVIDENCIAS.md).
- [Guía de despliegue en EC2](docs/DESPLIEGUE_EC2.md).

## Funcionamiento

```text
Navegador → HTTP → Docker → Gunicorn → Flask → yfinance → Yahoo Finance
```

En mi equipo, Docker conecta el puerto 5000 de Ubuntu con el puerto 5000 del contenedor. En EC2 se utilizará el puerto público 80 para acceder al mismo servicio.

## Archivos principales

| Archivo | Función |
| --- | --- |
| `read_value_yf.py` | Consulta bursátil, validaciones y ejecución por terminal |
| `app.py` | Rutas HTTP y manejo de errores |
| `templates/index.html` | Formulario y tabla de resultados |
| `requirements.txt` / `requirements.lock` | Dependencias directas y resolución completa de versiones |
| `gunicorn.conf.py` | Configuración del servidor HTTP |
| `Dockerfile` | Construcción de la imagen |
| `tests/` | Pruebas automatizadas con datos controlados |
| `scripts/verify_http.py` | Verificación de un servicio en ejecución |

## Instalación y ejecución local

Trabajé en Ubuntu 22.04 con Python 3.10. La imagen utiliza Python 3.11; las pruebas pasaron en ambas versiones. Para ejecutar el proyecto se necesitan Python, su módulo `venv` y acceso a Internet.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock
python -m pip check

# Consulta desde la terminal
python read_value_yf.py GOOGL --start 2024-01-01 --end 2024-02-01

# Servicio HTTP sin Docker
gunicorn --config gunicorn.conf.py --bind 127.0.0.1:5001 app:app
```

El servicio local se abre en [http://localhost:5001](http://localhost:5001). Reservé el puerto 5000 para la aplicación contenerizada. También se puede ejecutar `python app.py` en el puerto 5000 si está libre.

## Consultas HTTP

| Ruta | Respuesta |
| --- | --- |
| `/` | Tabla HTML con los últimos cinco registros y el promedio del período |
| `/api/stock` | Datos diarios y promedio en JSON |
| `/health` | Estado del proceso, sin consultar Yahoo Finance |

Las rutas de consulta aceptan `ticker`, `start` y `end`. Sus valores predeterminados son `GOOGL`, `2020-01-01` y la fecha actual. La fecha final es exclusiva.

```bash
curl --fail http://localhost:5000/health
curl --fail 'http://localhost:5000/api/stock?ticker=GOOGL&start=2024-01-01&end=2024-02-01'
```

Validé el símbolo bursátil, el formato de fechas y su orden. El intervalo máximo es de 3660 días. Las respuestas distinguen parámetros inválidos (400), ausencia de datos (404), fallos del proveedor (502), límite de consultas (503) y tiempo de espera agotado (504).

Conservé la función `get_stock_data(sd, stock, ed=None)` del enfoque del profesor. Utilicé `Ticker.history` para manejar los errores del proveedor y fijé `auto_adjust=False` para consultar precios sin ajuste automático.

## Pruebas

```bash
source .venv/bin/activate
python -m unittest discover -v

# Con el contenedor en ejecución: consulta real y reporte HTTP
python3 scripts/verify_http.py http://localhost:5000 \
  --report docs/evidencias/docker-http.json
```

Ejecuté **24 pruebas locales y las mismas 24 dentro de Docker**, todas satisfactorias. Las pruebas automatizadas utilizan datos controlados para comprobar validaciones, promedio, HTML, JSON y errores. La verificación HTTP consulta Yahoo Finance real y comprueba que el servicio responda correctamente.

## Construcción y ejecución con Docker

Con Docker instalado y en ejecución:

```bash
docker build -t stock-market:1.0 .
docker run -d --name taller1-stock-market \
  --read-only --tmpfs /tmp:rw,noexec,nosuid,size=128m \
  --cap-drop ALL --security-opt no-new-privileges:true \
  --memory 768m --cpus 1 --pids-limit 128 \
  --log-driver json-file --log-opt max-size=10m --log-opt max-file=3 \
  -p 127.0.0.1:5000:5000 stock-market:1.0

docker ps --filter name=taller1-stock-market
docker logs --tail 50 taller1-stock-market
docker inspect --format '{{json .State.Health}}' taller1-stock-market
```

La aplicación contenerizada se abre en [http://localhost:5000](http://localhost:5000). La imagen usa `python:3.11-slim-bookworm`, instala primero las dependencias para reutilizar esa capa y ejecuta Gunicorn con un usuario sin privilegios de administrador. `.dockerignore` limita los archivos que entran en la construcción y `.gitignore` excluye entornos, credenciales y claves.

Para repetir las pruebas dentro de la imagen sin acceso a Internet:

```bash
docker run --rm --network none --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=128m \
  --cap-drop ALL --security-opt no-new-privileges:true \
  --memory 768m --cpus 1 --pids-limit 128 \
  --mount "type=bind,source=$(pwd)/tests,target=/app/tests,readonly" \
  stock-market:1.0 python -m unittest discover -v
```

## Publicación en Docker Hub

Publiqué la imagen en [Docker Hub](https://hub.docker.com/r/yancertuche/stock-market) con esta secuencia:

```bash
docker tag stock-market:1.0 yancertuche/stock-market:1.0
docker login
docker push yancertuche/stock-market:1.0
```

`tag` asigna el nombre de mi cuenta y repositorio a la imagen; `login` autentica la cuenta; `push` transfiere las capas al registro. El digest obtenido al publicar identifica la versión exacta de la imagen y queda registrado en las evidencias.

Comprobé que puede descargarse sin iniciar sesión y que coincide con la imagen probada localmente. Para obtenerla:

```bash
docker pull yancertuche/stock-market:1.0
```

## Despliegue en AWS EC2

El siguiente paso es ejecutar esta imagen en una instancia Ubuntu amd64 y publicar el puerto `80:5000`. La [guía de EC2](docs/DESPLIEGUE_EC2.md) contiene la configuración de la VM, acceso SSH, instalación de Docker y verificación desde Internet.

Para comprobar el despliegue desde mi equipo:

```bash
python3 scripts/verify_http.py http://IP_PUBLICA \
  --report docs/evidencias/ec2-http.json
```

Con este recorrido aplico comunicación cliente-servidor, virtualización mediante contenedores, distribución de imágenes e infraestructura como servicio (IaaS).

Referencia del taller: `Act_7_Taller - 01 - Despliegue de Servicios v1.0.pdf`. Documentación técnica: [yfinance](https://ranaroussi.github.io/yfinance/reference/api/yfinance.Ticker.history.html), [Flask y Gunicorn](https://flask.palletsprojects.com/en/stable/deploying/gunicorn/) y [Docker en Ubuntu](https://docs.docker.com/engine/install/ubuntu/).
