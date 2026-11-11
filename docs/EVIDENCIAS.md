# Evidencias del Taller 1

**Autor:** yancertuche · **Fecha de las pruebas locales:** 10 de noviembre de 2026.

## Repositorios

- Código fuente: [yancertuche/taller1AWS](https://github.com/yancertuche/taller1AWS).
- Versión publicada: [commit dcbc85b](https://github.com/yancertuche/taller1AWS/commit/dcbc85b5b5e0ba7e5a00925ec3e3cc2593035c73).
- Imagen pública: [yancertuche/stock-market:1.0](https://hub.docker.com/r/yancertuche/stock-market).

## Resultados obtenidos

| Verificación | Resultado |
| --- | --- |
| Pruebas en Ubuntu, Python 3.10 | 24 pruebas satisfactorias |
| Pruebas en Docker, Python 3.11 y sin red | 24 pruebas satisfactorias |
| Dependencias | `pip check`: sin incompatibilidades |
| Aplicación contenerizada | `http://localhost:5000`, contenedor saludable |
| Ruta `/health` | HTTP 200 |
| Fecha inválida | HTTP 400 |
| Consulta JSON y tabla HTML con datos reales | HTTP 200 en ambas rutas |
| Publicación en Docker Hub | Etiqueta `1.0` publicada correctamente |
| Acceso público a la imagen | Lectura del manifiesto y `docker pull` sin credenciales satisfactorios |

Consulté **GOOGL** entre el **1 de enero y el 1 de febrero de 2024**, con fecha final exclusiva. Obtuve **21 registros** y un promedio de cierre de **143,84238**. También comprobé la página principal con sus parámetros predeterminados.

## Archivos de soporte

- [Verificación HTTP local](evidencias/local-http.json).
- [Verificación HTTP del contenedor](evidencias/docker-http.json).
- [Registro de pruebas](evidencias/pruebas.txt).
- [Metadatos de la imagen](evidencias/imagen-local.json).
- [Verificación pública de Docker Hub](evidencias/docker-hub.json).
- [Página HTML obtenida del contenedor](evidencias/docker-index.html).
- [Cabeceras de la respuesta HTTP](evidencias/docker-headers.txt).

Los informes HTTP registran consultas reales a Yahoo Finance. Las pruebas automatizadas usan datos controlados para verificar el comportamiento del código.

La imagen se publicó y verificó el **10 de noviembre de 2026**. Su digest es:

```text
sha256:141e42fb573c64bd1cfb1516e67224f529864005acde6aa96b81a42b4a96672c
```

## Despliegue público

Esta sección se completará al desplegar en EC2:

- Región e instancia utilizadas.
- URL pública del servicio.
- Informe `evidencias/ec2-http.json`.
- Captura del navegador con la URL y la tabla de resultados.

La dirección `localhost` corresponde a mi equipo; la URL de EC2 permitirá demostrar el acceso desde Internet.
