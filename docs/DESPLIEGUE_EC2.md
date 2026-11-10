# Plan de despliegue en EC2 (pendiente de autorización)

Este archivo prepara el despliegue; no acredita que exista una instancia ni que haya sido ejecutado. El script no se ha ejecutado en AWS.

**Modalidad acordada:** el estudiante operará la consola AWS y ejecutará los comandos remotos con acompañamiento. No se automatizará la creación ni la modificación de recursos desde el asistente. Los pasos se revisarán antes de cada acción que genere costos.

## Recorrido de aprendizaje en la consola

1. Entrar con una identidad IAM/Identity Center autorizada y elegir región. Revisar créditos, plan y facturación. Concepto: las regiones son ubicaciones de infraestructura y los precios dependen de la región y del recurso.
2. Ir a **EC2 → Instances → Launch instances**, escribir `taller1-stock-market` y escoger Ubuntu Server 24.04 LTS, arquitectura amd64. Concepto: la AMI define el sistema base de la VM; la imagen Docker define la aplicación, son artefactos distintos.
3. Seleccionar `t3.micro` y revisar el precio mostrado y la elegibilidad de la cuenta; disco gp3 cifrado de 8 GiB. Concepto: capacidad de cómputo y almacenamiento se cobran por separado. Configurar créditos de CPU `standard` en opciones avanzadas.
4. Seleccionar o crear la clave SSH acordada y guardarla fuera del repositorio. Concepto: autenticación asimétrica, clave pública en AWS y privada local.
5. Revisar VPC, subred, ruta pública y asignación automática de IPv4. Crear un grupo de seguridad dedicado con HTTP 80 público y SSH 22 con **My IP** (`/32`). Si la consola propone SSH desde Anywhere, corregirlo antes de continuar. Concepto: aislamiento de red y control de entrada.
6. En opciones avanzadas exigir IMDSv2 y hop limit 1; no adjuntar rol IAM ni secretos. Revisar el resumen de costos, recursos y reglas **antes de pulsar Launch instance**. Obtener autorización del estudiante para ese lanzamiento concreto.
7. Esperar estado running y comprobaciones de estado; identificar IP/DNS públicos. Concepto: IP privada para la red interna, IP pública para el cliente externo; puede cambiar al detener/iniciar.
8. Conectar por SSH verificando huella. Instalar Docker y ejecutar la imagen ya publicada con el procedimiento de abajo. Explicar cada comando antes de ejecutarlo; el script es una alternativa opcional revisable, no un paso obligatorio.
9. Verificar desde Ubuntu local, guardar URL/captura e informe HTTP. Concepto: una comprobación desde fuera demuestra la cadena de conectividad pública, además de la salud interna.
10. Revisar facturación y decidir cuándo detener o terminar. Obtener aprobación separada; no ejecutar limpieza automáticamente.

## Recursos propuestos

- Una instancia Ubuntu Server 24.04 LTS **amd64**, tipo `t3.micro` (2 vCPU, 1 GiB). Confirmar región, disponibilidad y presupuesto antes de crearla.
- Volumen raíz EBS gp3 de 8 GiB, cifrado, con eliminación al terminar la instancia.
- Una IPv4 pública asignada automáticamente; no hace falta Elastic IP.
- Una subred pública con ruta al Internet Gateway. Reutilizar VPC/subred existentes si son adecuadas; no crear NAT Gateway ni balanceador para este taller.
- Grupo de seguridad específico: TCP 80 desde `0.0.0.0/0` para la demostración pública; TCP 22 únicamente desde la IPv4 pública actual del estudiante con máscara `/32`. No abrir 5000 ni SSH al mundo. Evitar reglas IPv6 si no se utiliza IPv6.
- Salida a Internet para DNS, HTTPS (Docker Hub/Yahoo/paquetes) y HTTP/HTTPS para repositorios Ubuntu. Revisar las reglas existentes antes de cambiarlas.
- Clave SSH local fuera del repositorio, permisos `600`. Sin rol IAM para la aplicación: consultar Yahoo y descargar una imagen pública no requiere permisos AWS.
- IMDSv2 obligatorio; hop limit 1; créditos CPU `standard` para evitar cargos por créditos excedentes. Sin monitoreo detallado de pago.

La imagen se construye en amd64 local. No seleccionar `t4g`/ARM sin reconstruir y probar una imagen compatible.

## Costos y autorización

No asumir que la etiqueta del PDF de 2023 garantiza gratuidad hoy. Antes de lanzar: revisar el plan, créditos y elegibilidad actuales de la cuenta, región, precio On-Demand de `t3.micro`, almacenamiento y presupuesto.

La [tarifa publicada de IPv4 pública](https://aws.amazon.com/vpc/pricing/) consultada el 10 de noviembre de 2026 es **USD 0.005/hora por dirección**: USD 0.12 por 24 horas o USD 3.60 por 720 horas, antes de créditos/impuestos. A esto se suman instancia, EBS y posibles transferencias de salida. Consultar [EC2 On-Demand](https://aws.amazon.com/ec2/pricing/on-demand/), [EBS](https://aws.amazon.com/ebs/pricing/) y la [calculadora AWS](https://calculator.aws/). El costo total aún no está aprobado ni calculado para una región concreta.

Detener una instancia no equivale a terminarla: EBS, snapshots y direcciones reservadas pueden seguir facturándose. Terminar destruye recursos y no se hará sin autorización separada. La instrucción de limpieza del PDF es una referencia, no una autorización para eliminar.

## Ejecución después de autorizar

1. Confirmar si se reutiliza una instancia o se crea una nueva, región, IP de administración, presupuesto y clave pública. Autenticarse con IAM Identity Center o un usuario IAM de permisos limitados; evitar la cuenta root usada en el ejemplo histórico del PDF. Nunca compartir secretos en el chat.
2. Obtener aprobación del inventario exacto de recursos y reglas antes de modificar AWS. Si se usa la consola, revisar la pantalla final de lanzamiento. Con AWS CLI, revisar primero todos los parámetros y usar `--dry-run` cuando sea posible.
3. Crear o identificar los recursos autorizados. Anotar ID, región e IP/DNS en `docs/EVIDENCIAS.md`; guardar datos sensibles fuera de Git.
4. Publicar y verificar primero la imagen Docker Hub. Preferir una referencia inmutable `USUARIO/stock-market@sha256:DIGEST` para EC2; el script también acepta `:1.0`.
5. Verificar la huella SSH de la instancia por un canal AWS confiable antes de aceptar la primera conexión. No usar `StrictHostKeyChecking=no`. Ejecutar desde la raíz del proyecto, reemplazando los valores:

   ```bash
   chmod 600 "$HOME/.ssh/taller1-ec2.pem"
   scp -i "$HOME/.ssh/taller1-ec2.pem" deploy/ec2-bootstrap.sh ubuntu@IP_PUBLICA:/home/ubuntu/taller1-bootstrap.sh
   ssh -i "$HOME/.ssh/taller1-ec2.pem" ubuntu@IP_PUBLICA \
     'sudo bash /home/ubuntu/taller1-bootstrap.sh USUARIO/stock-market:1.0'
   ```

   El script instala Docker desde el repositorio oficial, descarga la imagen y publica HTTP 80 → 5000. Usa un proceso de aplicación sin root, capacidades eliminadas y raíz de solo lectura. No agrega al usuario `ubuntu` al grupo Docker, que confiere privilegios administrativos. No reemplaza contenedores existentes.

6. Verificar **desde el equipo local**, fuera de EC2:

   ```bash
   curl --fail --show-error http://IP_PUBLICA/health
   python3 scripts/verify_http.py http://IP_PUBLICA \
     --report docs/evidencias/ec2-http.json
   ```

   La verificación exige HTTP 200 con cotizaciones reales, tabla HTML y HTTP 400 para una fecha inválida. `/health` por sí solo no demuestra que Yahoo Finance responda. No usar `--fixture` para acreditar EC2. Abrir `http://IP_PUBLICA/` y guardar una captura de la tabla y URL, ocultando datos de cuenta. Este taller usa HTTP como el PDF; no enviar credenciales por esa conexión.

7. Si falla: consultar `sudo docker ps`, `sudo docker logs --tail 100 taller1-stock-market`, `sudo docker inspect --format '{{json .State.Health}}' taller1-stock-market`, `sudo ss -lntp`, reglas del grupo de seguridad, ruta pública y estado de la instancia. Un 503 de Yahoo indica límite externo; no abrir más puertos para corregirlo. Esperar y reintentar de forma moderada.
8. Registrar resultados reales y enlaces. Pedir autorización específica para detener o terminar la instancia cuando se haya entregado la evidencia. No ejecutar limpieza automática.

## Conceptos aplicados

EC2 representa IaaS y virtualización de hardware. Docker virtualiza procesos compartiendo el kernel del anfitrión. El grupo de seguridad controla el acceso de red; `80:5000` publica el servicio del contenedor en el puerto HTTP de la VM. Docker Hub distribuye el mismo artefacto que se probó localmente. Los registros y la ruta de salud permiten observar el proceso.

Fuentes: [instalación oficial Docker en Ubuntu](https://docs.docker.com/engine/install/ubuntu/), [reglas de grupos de seguridad EC2](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/security-group-rules-reference.html), [metadatos y user data](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-metadata.html). No almacenar secretos en user data.
