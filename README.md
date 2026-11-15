# cosknot

Marketplace de cosplay: un sitio donde quien hace piezas (ropa, props, pelucas y
accesorios) publica su trabajo y quien las busca las compra o las encarga a medida.



## índice

| apartado | documento |
|---|---|
| equipo y roles | [`docs/01-equipo.md`](docs/01-equipo.md) |
| la idea | [`docs/02-idea.md`](docs/02-idea.md) |
| mayor rival actual | [`docs/03-rival.md`](docs/03-rival.md) |
| matriz FODA | [`docs/04-foda.md`](docs/04-foda.md) |
| tablero kanban | [`docs/05-kanban.md`](docs/05-kanban.md) |
| diseño: nombre, logo, eslogan, tipografía, colores | [`docs/06-diseno.md`](docs/06-diseno.md) |
| CFO: ingresos, costes y punto de equilibrio | [`docs/07-cfo.md`](docs/07-cfo.md) |
| CTO: tecnologías, base de datos y despliegue | [`docs/08-cto.md`](docs/08-cto.md) |
| qué hace cada tecnología y qué contestar si preguntan | [`docs/09-preguntas.md`](docs/09-preguntas.md) |

## las tecnologías, en una tabla

| capa | lo que vamos a usar | por qué |
|---|---|---|
| lenguaje | **Python 3.13** | legible, un solo lenguaje para web y scripts |
| web | **Flask 3** + **Jinja2** | microframework: cada pieza se ve y se explica |
| base de datos | **PostgreSQL 16** en **Neon**, SQLite en local | el dominio es relacional y el SQL es el mismo |
| acceso a datos | **SQLAlchemy 2** + **Alembic** | sin SQL a mano; cada cambio de esquema versionado |
| estilos | **CSS propio** | sin dependencias ni compilación de frontend |
| fotos | **Cloudflare R2** (S3 compatible) | 10 GB gratis, servidor aparte para las imágenes |
| correo | **Resend** | avisos de pedido sin montar un servidor de correo |
| pagos | **Stripe Connect** | cobra el creador y nosotros la comisión, sin tocar el dinero |
| suscripción | **Stripe Checkout** | plan premium del taller y destacados de pago |
| IA | **Google Gemini** | sugerir la descripción de una pieza a partir de la foto |
| servidor | **gunicorn** | 2 workers y 4 hilos por instancia |
| despliegue | **Google Cloud Run** | escala solo de 0 a N instancias; sin servidor que administrar |
| tareas periódicas | **Cloud Run Jobs** + **Cloud Scheduler** | migraciones y cola de correos sin procesos encendidos |
| HTTPS | **certificado automático de Cloud Run** | lo emite y lo renueva la plataforma, gratis |
| DNS | **Cloudflare** en nube gris | resuelve `cosknot.me` y deja llegar la IP real del visitante |
| integración continua | **GitHub Actions** | nada se sube sin pasar las pruebas |

Coste de todo lo anterior: **0 €/mes**. Cloud Run y Neon están dentro de sus capas
gratuitas con cien veces de margen sobre lo que generaría un marketplace de 100 talleres, y
el dominio sale del pack de estudiante el primer año. Los 312 $ del pack siguen sin gastar,
como red por si algún día hay que pagar infraestructura.

El detalle, las alternativas que descartamos y las fuentes están en
[`docs/08-cto.md`](docs/08-cto.md).

## el equipo

| persona | rol |
|---|---|
| Daniel Barrasa | CEO y CMO |
| Jesús Larrazabal | CTO |
| Daniel Torres | CFO |

## estado del proyecto

- **hecho:** definición del producto, investigación de rivales, FODA, tablero, identidad
  visual y plan económico.
- **siguiente:** construir un prototipo de la portada, el listado y la ficha de una pieza.
- **nada está desplegado** y no hay ningún servicio contratado: todo lo de la tabla de
  arriba está elegido y presupuestado, no instalado.

Los importes de esta entrega están calculados a **14 de noviembre de 2026**, con las
tarifas públicas de cada servicio.
