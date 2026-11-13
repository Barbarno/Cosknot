# stack, hosting, base de datos y dominio

fecha: 2026-11-12
estado: **sustituida en hosting y base de datos por `0003-heroku-hosting.md`**

Lo que sigue es la decisión original (Render + Neon, 0 €/mes). Se conserva como
histórico: el despliegue actual es Heroku con Heroku Postgres, 12 $/mes. Python,
Flask, Jinja, gunicorn y SQLite solo en local siguen vigentes.

## decisión

- Lenguaje: Python 3.13 con Flask y Jinja.
- Servidor: gunicorn con un `wsgi.py`.
- Hosting: Render, plan free.
- Base de datos: Neon, PostgreSQL free.
- Dominio: `cosknot.onrender.com` desde el primer día y `cosknot.duckdns.org` gratis
  para tener un nombre más corto.
- HTTPS: el certificado automático de Render con Let's Encrypt.
- Descartado para la primera versión: AWS, Azure, Fly.io, Oracle, No-IP y SQLite en
  Render.

Coste: 0 € al mes y sin tarjeta.

## por qué

- **Python** porque es lo que estamos aprendiendo y ya estaba en el roadmap. Flask con
  Jinja renderiza en el servidor, que es lo más fácil de seguir cuando empiezas.
- **Render** porque es de los pocos gratis que ejecuta Flask normal, sin tarjeta, con
  subdominio, dominio propio y HTTPS.
- **Neon** porque es PostgreSQL de verdad, 1 GB y sin tarjeta. El PostgreSQL de Render
  caduca a los 30 días y Supabase se pausa a la semana.
- **DuckDNS** porque es gratis y deja un registro A, que es lo que Render necesita para
  un dominio que considera apex.

## alternativas que miré

- **Cloud Run**: mejor arranque y más CPU, pero pide tarjeta, Docker y no tiene tope de
  gasto. Se revisa si el arranque en frío de Render molesta.
- **Oracle Always Free**: mucha máquina gratis, pero pide tarjeta, hay poca capacidad y
  da trabajo de administración.
- **PythonAnywhere**: no duerme y no pide tarjeta, pero no deja dominio propio.
- **Supabase**: plan B de base de datos si la web se usa todos los días.
- **SQLite en Render**: descartado, el disco es efímero y la base se borra en cada
  despliegue.
- **AWS y Azure**: descartados por coste y por líos de tarjeta.
- **Vercel y Netlify**: no ejecutan Flask de forma natural.

## cuándo revisar esto

- Si el arranque en frío molesta a los usuarios, toca Cloud Run.
- Si cosknot empieza a vender o a recibir tráfico real, comprar un `.dev` y salir del
  subdominio gratuito.
- Si la base pasa de 1 GB o de 100 horas de cómputo al mes, pasar a un plan de pago.
- Si hay que guardar muchas imágenes, usar un almacenamiento aparte.

## cómo salió al final

Lo que se construyó, comparado con lo planeado. Los pasos reales están en
`docs/deployment.md`.

| qué | planeado | real |
|---|---|---|
| hosting | Render free | Render free en Frankfurt, servicio creado desde Public Git Repository con autodespliegue |
| Python | 3.12 o 3.13 con Flask y gunicorn | 3.13.17, gunicorn con `--workers 2 --threads 4` |
| base de datos | Neon free | Neon en Frankfurt, PostgreSQL 18, con la cadena pooled |
| esquema | no estaba en el plan | `create_all()` y seed al arrancar, sin migraciones |
| dominio | `cosknot.onrender.com` y luego uno gratis | `cosknot.onrender.com` y `cosknot.duckdns.org` |
| CI/CD | no estaba en el plan | pruebas en cada push, despliegue por API y copia semanal |

- **Coste real**: 0 € al mes, sin tarjeta en Render ni en Neon.
- **Lo que no vio el plan**: Render trata el subdominio de DuckDNS como apex y espera un
  registro A, no un CNAME. Por eso el dominio se configura con un A a `216.24.57.1`.
- El resto sigue igual: Python con Flask y Jinja, gunicorn, y SQLite solo en local.
