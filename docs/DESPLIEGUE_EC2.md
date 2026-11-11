# Despliegue del servicio en AWS EC2

Mi objetivo en esta etapa es ejecutar en una máquina virtual la misma imagen que probé localmente. Realizaré la configuración desde la consola de AWS para reconocer los recursos y su función.

## Configuración de la instancia

| Recurso | Configuración |
| --- | --- |
| Sistema operativo | Ubuntu Server 24.04 LTS, arquitectura amd64 |
| Tipo de instancia | `t3.micro`, sujeto a disponibilidad y presupuesto |
| Almacenamiento | EBS gp3 de 8 GiB, cifrado |
| Red | Subred pública con salida a Internet e IPv4 pública |
| HTTP | TCP 80 desde Internet |
| SSH | TCP 22 únicamente desde mi IP pública (`/32`) |
| Clave privada | Fuera del repositorio, permisos `600` |
| Metadatos | IMDSv2 obligatorio, hop limit 1 |

La arquitectura amd64 coincide con la imagen construida en mi equipo. No es necesario un balanceador, un NAT Gateway ni un rol IAM para consultar Yahoo Finance y descargar una imagen pública.

## Pasos en la consola

1. Elegir la región y revisar el plan, créditos y precios de la cuenta.
2. Abrir **EC2 → Instances → Launch instances** y asignar el nombre `taller1-stock-market`.
3. Seleccionar Ubuntu, `t3.micro` y el disco de la tabla. Configurar créditos de CPU `standard`.
4. Seleccionar o crear la clave SSH y guardarla localmente.
5. Revisar la VPC, la subred y la asignación de IP pública. Configurar el grupo de seguridad con HTTP público y SSH desde **My IP**.
6. Revisar el resumen y lanzar la instancia. Esperar a que las comprobaciones de estado sean satisfactorias.
7. Copiar la IP pública y conectarse por SSH, verificando la huella del servidor.

## Instalar Docker y ejecutar la imagen

El archivo `deploy/ec2-bootstrap.sh` instala Docker desde su repositorio oficial y ejecuta la imagen con el puerto `80:5000`. Desde la raíz del proyecto, reemplazando `IP_PUBLICA`:

```bash
chmod 600 "$HOME/.ssh/taller1-ec2.pem"
scp -i "$HOME/.ssh/taller1-ec2.pem" deploy/ec2-bootstrap.sh \
  ubuntu@IP_PUBLICA:/home/ubuntu/taller1-bootstrap.sh
ssh -i "$HOME/.ssh/taller1-ec2.pem" ubuntu@IP_PUBLICA \
  'sudo bash /home/ubuntu/taller1-bootstrap.sh yancertuche/stock-market:1.0'
```

El contenedor ejecuta la aplicación sin root, limita recursos y se reinicia si Docker o la VM vuelven a arrancar. El script conserva los contenedores existentes en lugar de reemplazarlos.

## Verificar desde mi equipo

```bash
curl --fail http://IP_PUBLICA/health
python3 scripts/verify_http.py http://IP_PUBLICA \
  --report docs/evidencias/ec2-http.json
```

Abrir `http://IP_PUBLICA/` y guardar una captura con la tabla. La prueba debe comprobar tanto el proceso como la consulta real a Yahoo Finance. Registrar la URL y los resultados en [EVIDENCIAS.md](EVIDENCIAS.md).

Si falla, revisar el estado de la instancia, el grupo de seguridad y `sudo docker logs --tail 50 taller1-stock-market`. Un error 503 de Yahoo Finance indica un límite del proveedor.

## Costos

EC2, el disco EBS, la IPv4 pública y algunas transferencias pueden generar cargos. Antes del lanzamiento revisaré los precios de la región y los créditos de mi cuenta. Detener la VM no elimina el disco; su almacenamiento puede seguir facturándose.

Referencias: [precios EC2](https://aws.amazon.com/ec2/pricing/on-demand/), [precios EBS](https://aws.amazon.com/ebs/pricing/), [precios IPv4](https://aws.amazon.com/vpc/pricing/), [reglas de seguridad](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/security-group-rules-reference.html) e [instalación Docker](https://docs.docker.com/engine/install/ubuntu/).
