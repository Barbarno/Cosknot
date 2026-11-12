# despliegue, base de datos, dominio y HTTPS gratis

Apuntes de la investigación que hice antes de montar cosknot, resumidos. La decisión
final está en `docs/decisions/0001-stack-despliegue-dominio.md`.

## qué necesitaba

- Poder publicar una web Flask sin pagar nada ni poner tarjeta.
- Una base de datos que no se borre en cada despliegue.
- Un dominio decente y HTTPS.
- Que se pueda seguir en el futuro sin rehacerlo todo.

## lenguaje

Python con Flask, porque es lo que estamos dando en clase y hay mucha documentación.
Node o PHP no aportaban nada para este proyecto.

## hosting

Render es de los pocos que cumplen todo:

- Ejecuta Flask normal, con gunicorn y un `wsgi.py`.
- Tiene plan free sin tarjeta.
- Da subdominio propio y HTTPS.
- Permite dominio personalizado.

Contras: el plan free duerme el servicio a los 15 minutos sin tráfico y la primera
visita tarda unos 50 segundos. También da 5 GB de banda al mes.

Otras opciones que miré:

- **PythonAnywhere**: no duerme y no pide tarjeta, pero no deja poner dominio propio.
- **Cloud Run**: mejor arranque, pero pide tarjeta, Docker y no tiene tope de gasto.
- **Oracle Always Free**: mucha máquina, pero pide tarjeta y da trabajo de administrar.
- **Vercel y Netlify**: no ejecutan Flask de forma natural.

## base de datos

Neon, PostgreSQL gratis, 1 GB y sin tarjeta. El PostgreSQL de Render caduca a los 30
días, y Supabase se pausa si no se usa en una semana.

Hay que usar la cadena que lleva `-pooler`, porque si no se agotan las conexiones
directas del plan free. La pega: el pooler va en modo transacción y no guarda estado
de sesión, así que hay que desactivar la caché de prepared statements de psycopg3.

El plan free también son 100 horas de cómputo al mes. Si algo toca la base muy a
menudo, se gasta y el proyecto se suspende hasta el mes siguiente.

## dominio y HTTPS

DuckDNS es gratis y deja un registro A, que es lo que Render espera para este dominio.
No deja CNAME, pero tampoco hace falta. HTTPS lo pone Render con Let's Encrypt en
cuanto verifica el dominio.

También probé is-a.dev, pero su norma es que el sitio sea de desarrollo de software y
prohíbe el uso comercial, así que cosknot no encaja. Se queda como reserva en
`domains/cosknot.json`.

## límites reales del plan free

- Render duerme el servicio a los 15 minutos sin tráfico.
- Render da 5 GB de banda al mes.
- Neon da 1 GB de almacenamiento y 100 horas de cómputo al mes.
- No hay copias de seguridad automáticas de Neon; por eso el workflow del domingo hace
  un `pg_dump`.

## fuentes

- Documentación de Render: https://render.com/docs
- Documentación de Neon: https://neon.tech/docs
- DuckDNS: https://www.duckdns.org
- is-a.dev: https://www.is-a.dev
