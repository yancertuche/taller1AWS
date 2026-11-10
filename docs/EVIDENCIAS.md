# Evidencias del Taller 1

Fecha: **10 de noviembre de 2026**, zona horaria `America/Bogota` (UTC−05:00). Registrar únicamente operaciones realmente ejecutadas.

## Etapas locales ejecutadas

| Comprobación | Resultado observado |
| --- | --- |
| Documento del profesor | PDF original leído con `pdftotext`; se conserva fuera del repositorio |
| Sistema | Ubuntu 22.04.5 LTS, amd64, Python 3.10.12 |
| Git | 2.34.1, rama `main`, remoto `https://github.com/yancertuche/taller1AWS.git`, sin ramas remotas al inspeccionar |
| Herramientas | Docker 28.1.1, Compose 2.35.1, GitHub CLI instalado y autenticado; AWS CLI ausente |
| Dependencias | Instaladas en `.venv`; `pip check` respondió `No broken requirements found` |
| Tests Python local | `python -m unittest discover -v`: **24 pruebas, OK** |
| Gunicorn local | Dos workers, `http://127.0.0.1:5001` |
| HTTP local con Yahoo real | `/health` 200; fecha inválida 400; JSON bursátil 200; tabla HTML 200 |
| Imagen Docker | `stock-market:1.0`, construida correctamente con Python 3.11 |
| Tests en imagen sin red | **24 pruebas, OK**, con `--network none` y fixtures artificiales |
| Contenedor de servicio | `taller1-stock-market`, publicado solo en `127.0.0.1:5000`, estado observado `healthy` |
| HTTP Docker con Yahoo real | `/health` 200; fecha inválida 400; JSON bursátil 200; tabla HTML 200 |

Los tests simulan al proveedor; las verificaciones HTTP consultaron Yahoo Finance real. Ambos tipos de prueba tienen objetivos distintos y están identificados en los informes.

Consulta real utilizada: **GOOGL**, `2024-01-01 <= fecha < 2024-02-01`. Se obtuvieron **21 registros** y una media de cierre aproximada de **143.8423803420294**. Los informes registran el resultado observado; una nueva consulta puede variar por revisiones del proveedor.

- [Informe HTTP local](evidencias/local-http.json).
- [Informe HTTP Docker](evidencias/docker-http.json).
- [Registro de pruebas locales y Docker](evidencias/pruebas.txt).
- [Metadatos de la imagen local](evidencias/imagen-local.json), también etiquetada localmente `yancertuche/stock-market:1.0`.
- [HTML capturado desde `/` sin parámetros](evidencias/docker-index.html): HTTP 200, 1723 registros para el intervalo predeterminado, con cinco filas visibles.
- [Cabeceras HTTP de esa respuesta](evidencias/docker-headers.txt), conservadas con saltos de línea normalizados a LF para Git.
- ID de la imagen local construida: `sha256:00b4a58a176672a66d3cdcb6e2fd87437c4adb25c554d48a8524f229dd35caf7`.
- Digest observado de la base: `python:3.11-slim-bookworm@sha256:a83ba18aef0f865b1a4a611c2cf460fe446f2795673bbb9fe43be570439e3b39`.

## Enlaces de entrega y trabajo pendiente

| Entregable | Destino o resultado | Estado |
| --- | --- | --- |
| Código fuente | [GitHub: yancertuche/taller1AWS](https://github.com/yancertuche/taller1AWS) | Preparado; publicación pendiente de autorización |
| Commit publicado | Pendiente de push y verificación del SHA remoto | Pendiente |
| Imagen pública | [Docker Hub: yancertuche/stock-market](https://hub.docker.com/r/yancertuche/stock-market), etiqueta prevista `1.0` | Preparada; publicación pendiente de autorización |
| Digest remoto Docker Hub | Pendiente de push; no confundir con el ID local | Pendiente |
| Instancia EC2 | El estudiante realizará los pasos en la consola AWS con acompañamiento | Pendiente |
| Región, tipo e ID EC2 | Confirmar antes de lanzar | Pendiente |
| URL pública | Todavía no existe una URL EC2 verificada | Pendiente |
| Verificación HTTP desde fuera de AWS | Generar `evidencias/ec2-http.json` sin `--fixture` | Pendiente |
| Captura de navegador público | Mostrar URL y tabla, ocultando datos privados de cuenta | Pendiente |
| Revisión de recursos al terminar | Requiere autorización específica antes de detener/eliminar | Pendiente |

Los enlaces GitHub y Docker Hub representan los destinos acordados; **no son prueba de una publicación ya realizada**. Las URLs `127.0.0.1` son accesibles solo desde el equipo local y no sustituyen la URL pública.

## Qué presentar al profesor

1. URL del repositorio con README, código, Dockerfile y pruebas; enlace al commit entregado.
2. URL pública Docker Hub, etiqueta utilizada y digest de manifiesto publicado.
3. URL HTTP pública de EC2 y captura de la tabla con datos reales.
4. Informe HTTP público con fecha, resultados y `passed: true`.
5. Evidencia de tests locales y dentro del contenedor, más el estado de salud.
6. Explicación de proceso → servicio HTTP → contenedor → registro → VM en nube.

No adjuntar archivos de claves, credenciales AWS, tokens, contraseñas ni capturas que los expongan. El directorio `docs/evidencias/privado/` está excluido de Git; revisar también manualmente cada evidencia pública.
