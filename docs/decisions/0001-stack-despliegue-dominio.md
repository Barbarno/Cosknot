# stack, hosting, base de datos y dominio para la v1

fecha: 2026-11-12
estado: aceptada

## decisión

- lenguaje: **python 3.12/3.13 + flask + jinja** (se mantiene lo que ya fija el roadmap).
- servidor: **gunicorn** con un `wsgi.py`.
- hosting: **render, plan free**.
- base de datos: **neon, postgres free**.
- dominio: **`cosknot.onrender.com`** desde el día uno y **`cosknot.is-a.dev`** gratis cuando se quiera un nombre bonito.
- https: **el tls automático de render** (let's encrypt).
- descartados para la v1: aws, azure, fly.io, oracle, no-ip, duckdns, sqlite en render.

coste: 0 €/mes y sin tarjeta.

## motivo

- **python porque es lo que el equipo ya aprende y el roadmap ya fija**. cambiar a node, go o php añade curva y tooling sin resolver nada del mvp. flask + jinja renderiza en servidor, que es lo más fácil de seguir para un principiante.
- **render porque es el único free que ejecuta flask normal, sin tarjeta, con subdominio, dominio propio y https**. además sus terms no prohíben uso comercial; los docs solo recomiendan no usarlo en producción.
- **neon porque es postgres de verdad, 1 gb, sin tarjeta y sin pausa de proyecto**. render postgres caduca a los 30 días y supabase se pausa a la semana y no tiene backups.
- **is-a.dev porque es el único dominio gratis que acepta un cname a render** y está en la public suffix list, así que cloudflare y el https funcionan. no-ip obliga a confirmar cada 30 días y duckdns no acepta cname.
- **no-ip no aplica**: es dns dinámico para hostear en casa, no una alternativa a aws.

## alternativas

- **cloud run**: mejor cold start (~3 s) y más cpu, pero exige tarjeta, docker y no tiene tope de gasto. se revisa si el cold start de render molesta.
- **oracle always free**: 2 ocpu/12 gb y 10 tb de egress, pero tarjeta, capacidad arm limitada, reclamo de instancias ociosas y faena de sysadmin. no para el mvp.
- **pythonanywhere**: no duerme y no pide tarjeta, pero no permite dominio propio y bloquea la salida a internet por whitelist. solo si el dominio no importa.
- **supabase**: plan b de db si la app se usa todos los días; no tiene reloj de cuotas pero se pausa a la semana y no tiene backups.
- **aiven**: plan b de db si se quiere postgres siempre encendido sin tarjeta; 1 gb y 20 conexiones.
- **sqlite en render**: descartado porque el filesystem es efímero y la db se borra en cada deploy.
- **aws y azure**: descartados por coste/riesgo real. azure f1 no permite dominio propio y tiene 165 mb de banda; aws ya no da 12 meses gratis a cuentas nuevas.
- **vercel y netlify**: descartados para cosknot; vercel hobby prohíbe uso comercial y netlify no ejecuta flask de forma natural.

## revisar si

- el cold start de 1 minuto molesta a los usuarios → cloud run u oracle.
- cosknot empieza a vender o a recibir tráfico real → comprar `.dev` (~8-12 $/año) y salir de is-a.dev.
- la db pasa de 1 gb o de 100 cu-horas al mes → neon de pago, supabase o aiven.
- hay que guardar muchas imágenes → cloudflare r2 (10 gb gratis).
- render, neon o is-a.dev cambian sus condiciones.

## referencia

investigación completa con fuentes y anécdotas: `docs/research/despliegue-gratis-2026.md`.
