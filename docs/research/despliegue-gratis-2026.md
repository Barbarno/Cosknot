# despliegue, base de datos, dominio y https gratis

fecha: 2026-11-12
estado: investigación cerrada. decisión en `docs/decisions/0001-stack-despliegue-dominio.md`.

datos verificados contra documentación oficial y, cuando se indica, contra foros y experiencias reales. los free tiers cambian sin avisar: mira la fecha antes de fiarte. lo que va marcado como **anécdota** no es una garantía, es lo que reporta la gente.

## 0. conceptos, para que se entienda el resto

si vienes de azure y aws, este es el mapa:

- **iaas** (aws ec2, azure vm, oracle compute): te dan una máquina y tú instalas todo. máximo control, máxima faena. es lo que ya conoces.
- **paas** (render, cloud run, app service): le das el repo y ellos ejecutan la app. tú no tocas servidores. es lo que nos interesa.
- **dns**: traduce `cosknot.is-a.dev` al servidor real. un registro **a** apunta a una ip; un **cname** apunta a otro nombre. para un paas se usa cname porque la ip del paas cambia.
- **tls/https**: el candado del navegador. lo emite let's encrypt o la plataforma y se renueva solo.
- **base de datos gestionada**: un postgres que corre en otro sitio; te conectas por una url. tú no haces backups ni actualizaciones (aunque deberías hacer copia igual).
- **cold start**: si el plan gratis duerme la app por inactividad, el primer visitante espera a que arranque. en render, ~1 minuto.
- **free permanente vs trial**: aws y azure regalan créditos durante meses. render, neon, supabase y oracle tienen capas gratuitas que no caducan, con límites.
- **tarjeta de verificación**: algunos proveedores la piden para crear la cuenta aunque el plan sea gratis. suelen hacer un cargo temporal de 1 $ que se devuelve. no es un pago.

## 1. resumen de la decisión

| pieza | elegido | por qué gana |
|---|---|---|
| lenguaje | python + flask + jinja | es el que el equipo ya aprende y el roadmap ya fija; sin build ni tooling extra |
| hosting | render, plan free | ejecuta flask nativo, da subdominio y https, 2 dominios propios, no pide tarjeta y sus terms no prohíben uso comercial |
| base de datos | neon, postgres free | 1 gb, sin tarjeta, no pausa el proyecto, scale-to-zero y 6 h de historial |
| dominio | `cosknot.is-a.dev` gratis; `cosknot.onrender.com` de respaldo | es el único dominio gratis que se puede apuntar a render con un cname y lo acepta cloudflare |
| https | tls automático de render | let's encrypt gestionado, renovación automática, cero configuración |
| no-ip | descartado | no-ip es dns dinámico para hostear en casa; aquí no hace falta |

coste del mvp: 0 €/mes. no hace falta tarjeta en ninguna de las tres piezas elegidas. la letra pequeña está en el punto 7.

## 2. lenguaje de programación

el repo ya fija python + flask + jinja + sqlite en `docs/cosknot-roadmap.md`. se mantiene.

por qué python:

- **python** es la ruta de aprendizaje del equipo (`docs/context.md`). flask + jinja renderiza html en el servidor, que es lo más fácil de entender de punta a punta para un principiante.
- **node/typescript** tiene más ecosistema, pero añade build, dependencias y un modelo mental nuevo. no compensa en un mvp de descubrimiento de creadores.
- **go** es rápido y despliega en un binario, pero la curva de aprendizaje frena al equipo.
- **php** es lo más barato de hostear en shared hosting, pero nadie del equipo lo usa.

para que render ejecute flask necesita un servidor wsgi: `gunicorn`. en local, python no viene instalado en esta máquina (el alias de la microsoft store está roto). instala 3.12 o 3.13 desde https://www.python.org/downloads/ y marca "add python to path".

fuentes: `docs/cosknot-roadmap.md`, `docs/context.md`.

## 3. hosting

| plataforma | gratis 2026 | límites | duerme | dominio propio + https | tarjeta | riesgo de cobro |
|---|---|---|---|---|---|---|
| **render** | web service 512 mb / 0.1 cpu, 750 h/mes, 5 gb banda | fs efímero; postgres free caduca a los 30 días | sí, 15 min; ~1 min de arranque | sí, 2 dominios y tls | no | 0 |
| **cloudflare pages + workers** | pages estático ilimitado; workers 100k req/día | 10 ms cpu/invocación, 128 mb | no | sí | no verificado | 0 |
| **vercel** | hobby: 100 gb, 1m invocaciones | **solo uso personal no comercial** | no | sí | no verificado | 0 |
| **netlify** | 300 créditos/mes | ~15 gb de banda, créditos por función | no | sí | no | 0 |
| **pythonanywhere** | 1 web app, 512 mb disco, 100 cpu-s/día | solo `usuario.pythonanywhere.com`; salida a internet por whitelist; sin ssh ni tareas | no | **no** | no | 0 |
| **fly.io** | no hay free real | waiver si la factura <5 $/mes; si llega a 5, pagas los 5 | configurable | sí | sí | **sí** |
| **oracle always free** | 2 ocpu/12 gb arm + 200 gb + 10 tb egress | te reclaman la vm si está ociosa; capacidad arm agotada | no | sí, lo montas tú | sí (móvil + tarjeta) | bajo, pero cierran cuentas |
| **google cloud run** | 2m req, 180k vcpu-s, 360k gib-s/mes | por cuenta de facturación; cloud build y artifact registry se cobran aparte | scale-to-zero (~3 s medidos) | sí | sí | **sí, sin tope duro** |
| **azure app service f1** | 60 cpu-min/día, 1 gb ram | **165 mb de banda**, sin dominio propio ni ssl custom, 32-bit | no | **no** | sí | bajo |
| **aws** | 100 $ + hasta 100 $ en créditos, **6 meses** | sin vm always-free para cuentas nuevas; route 53 se paga | cold start | no incluido | no | no permanente |
| **deno deploy** | 1m req/mes | cierra en abril 2027 | no | sí | no verificado | 0 |
| **github pages** | estático en repos públicos | 1 gb, 100 gb/mes | n/a | sí | no | 0 |

### por qué render

- **es el único que ejecuta flask normal, gratis, sin tarjeta y con dominio propio + tls**. los demás fallan en algo: cloud run pide tarjeta y contenedor; oracle pide ser sysadmin; azure f1 no permite dominio propio; vercel hobby prohíbe uso comercial.
- **sus terms no prohíben vender**. verificado en https://render.com/terms (actualizado 2026-07-10): la palabra "commercial" solo aparece en la cláusula de arbitraje. los docs recomiendan no usarlo en producción, pero es una recomendación, no una prohibición.
- **el cold start es el precio**: 15 min sin tráfico y el primer request tarda ~1 min. para un mvp y una demo, se acepta. si molesta, en el punto 3.1 hay alternativas con tarjeta.

anécdotas: hay reportes en reddit de servicios free suspendidos por "service-initiated traffic" si la app hace muchas peticiones salientes (db externa, cron, webhooks). no pude abrir los hilos completos (reddit bloquea), así que tómalo como rumor consistente, no como hecho. con neon vas a hacer tráfico saliente, pero poco.

### 3.1. si aceptas tarjeta (sin pagar)

- **cloud run**: mejor rendimiento y cold start de ~3 s, pero exige docker y una cuenta de facturación. **no tiene tope de gasto** y cloud build/artifact registry se cobran aparte. es la opción si quieres aprender algo de trabajo real y aceptas revisar la factura.
- **oracle always free**: el mejor hardware gratis que existe (2 ocpu/12 gb, 200 gb, 10 tb de egress). pegas: tarjeta y móvil, capacidad arm agotada al crear la vm, y **te reclaman la instancia si 7 días está por debajo del 20% de cpu, red y memoria**. para un flask de juguete, entra en esa definición. es para aprender ops, no para "que esté online y ya".
- **fly.io**: ya no hay free. es un waiver: si la factura es menor de 5 $, no la cobran; si llega a 5, pagas los 5. una máquina always-on de 256 mb son 2.19 $/mes. sin tope de gasto.

### 3.2. por qué no azure ni aws (que es lo que conoces)

- **azure app service f1** es un juguete para flask: 165 mb de banda al día, sin dominio propio, sin ssl custom y 32-bit. no sirve para un proyecto real.
- **azure free account** son 200 $ durante 30 días y tarjeta; después, pay-as-you-go. **azure for students** son 100 $/12 meses sin tarjeta, pero uso educativo y no comercial.
- **azure container apps** da 180k vcpu-s y 2m requests por suscripción, pero hay casos verificados de cobros por dejar el `min scale` mal configurado (stack overflow 77382203). para un principiante, factura sorpresa.
- **aws** ya no da la capa gratis de 12 meses a cuentas nuevas: son 100 $ + hasta 100 $ de crédito durante **6 meses**, y no hay vm always-free. route 53 se paga. no es una opción "gratis" para este proyecto.

resumen: azure y aws están pensados para que alguien pague la factura. para un mvp de aprendizaje, son más caros en tiempo y en riesgo que render.

fuentes:
- https://render.com/docs/free
- https://render.com/docs/custom-domains
- https://render.com/terms
- https://developers.cloudflare.com/workers/platform/limits/
- https://vercel.com/docs/plans/hobby
- https://www.netlify.com/pricing/
- https://www.pythonanywhere.com/pricing/
- https://www.pythonanywhere.com/whitelist/
- https://docs.fly.io/about/free-waiver
- https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm
- https://cloud.google.com/run/pricing
- https://learn.microsoft.com/en-us/azure/azure-resource-manager/management/azure-subscription-service-limits#azure-app-service-limits
- https://stackoverflow.com/questions/77382203/
- https://aws.amazon.com/free/
- https://aws.amazon.com/free/free-tier-faqs/
- https://news.ycombinator.com/item?id=49183750 (recorte de oracle)
- https://news.ycombinator.com/item?id=46238860 (cold starts medidos)

## 4. base de datos

| proveedor | gratis 2026 | límites | se pausa | tarjeta | veredicto |
|---|---|---|---|---|---|
| **neon** (postgres) | 1 gb, 100 cu-horas/proyecto/mes, 5 gb egress | al agotar cu-horas se suspende el compute hasta el mes siguiente | scale-to-zero a los 5 min | no | **elegido** |
| **supabase** (postgres) | 500 mb db, 1 gb storage, 2 proyectos | sin backups; ipv4 solo por pooler | **sí, 7 días sin actividad** | no | plan b si la app se usa a diario |
| **aiven** (postgres) | 1 gb disco, 1 cpu, 1 gb ram | 20 conexiones, sin pooling | puede apagarse por inactividad | no | plan b si quieres postgres siempre encendido |
| **turso** (sqlite) | 5 gb, 500m lecturas/mes | comprado por supabase el 2026-10-02 | no | no | no: no es postgres y su futuro es incierto |
| **cloudflare d1** (sqlite) | 500 mb por db, 5 gb por cuenta | 100k escrituras/día **hard stop**, single-threaded, sin transacciones interactivas | no | no verificado | no |
| **mongodb atlas** | 512 mb, 100 ops/s | pausa a los 30 días sin conexiones | sí | no verificado | no: no es postgres |
| **cockroachdb** | **ya no hay free** para cuentas nuevas | trial de 30 días / 400 $ desde 2026-09-15 | sí, al acabar | trial | no |
| **oracle autonomous** | 2 db de 20 gb | stop a los 7 días, borrado a los 90 | sí | sí | no |
| **planetscale** | **no hay free** desde abr-2024 | desde 5 $/mes | n/a | sí | no |

### por qué neon

- **1 gb de postgres, sin tarjeta, sin pausa de proyecto y con 6 h de historial + 1 snapshot manual**. supabase no tiene backups y aiven solo 1 gb.
- **scale-to-zero**: si nadie usa la app, la db se duerme y no gasta cuota. encaja con render, que también duerme.
- **la cuota es un reloj de arena**: 100 cu-horas a 0.25 cu (mínimo) = 400 h. un mes tiene ~730 h. si la db está despierta 24/7, te quedas sin cuota sobre el día 16 y te suspenden el compute. **no le pongas un keep-alive**: es el error contrario al de supabase.
- cold start medido en free: ~1.1 s (anécdota hn 40941304). oficial dice "cientos de milisegundos".
- usa el connection string con `-pooler` (pgbouncer, transaction mode) y `pool_pre_ping` en sqlalchemy. el pooler **no soporta** `SET`, `LISTEN/NOTIFY`, temp tables ni prepared statements a nivel sql.

### cuándo cambiar

- si la app se usa todos los días y la db está despierta muchas horas → **supabase free** (no tiene reloj de cuotas) o **aiven free** (siempre encendido, 20 conexiones). en supabase, pon un cron diario que haga `select 1` y un `pg_dump` nocturno, porque no hay backups y hay anécdotas de db en blanco tras una pausa larga.
- si quieres postgres en una vm tuya → oracle. pero entonces eres tú el dba.

fuentes:
- https://neon.com/docs/introduction/plans
- https://neon.com/docs/introduction/scale-to-zero
- https://neon.com/docs/connect/connection-pooling
- https://neon.com/docs/connect/connection-latency
- https://status.neon.tech/
- https://supabase.com/pricing
- https://supabase.com/docs/guides/platform/free-project-pausing
- https://supabase.com/docs/guides/database/connecting-to-postgres
- https://github.com/supabase/supabase/issues/48819
- https://aiven.io/docs/products/postgresql/concepts/pg-free-tier
- https://turso.tech/blog/turso-is-joining-supabase
- https://developers.cloudflare.com/d1/platform/limits/
- https://www.cockroachlabs.com/pricing/
- https://www.mongodb.com/pricing
- https://planetscale.com/pricing
- https://news.ycombinator.com/item?id=40941304 (cold start de neon)

## 5. dominio, dns, no-ip y https

primero, la confusión: **no-ip no es una alternativa a aws**. no-ip es dns dinámico para cuando hosteas en tu casa y tu ip cambia. aws es un proveedor cloud. son problemas distintos. para cosknot, que va a un paas, no-ip no hace falta.

| servicio | gratis | límites | tipo | renovar | tarjeta | veredicto |
|---|---|---|---|---|---|---|
| **is-a.dev** | `cosknot.is-a.dev` | revisión por pr; solo dev y no comercial | solo subdominio | no | no | **elegido** |
| **render** | `cosknot.onrender.com` | el subdominio no es tuyo | subdominio | no | no | respaldo |
| **no-ip free** | 1 hostname ddns | confirmar cada 30 días o lo pierdes | solo subdominio | **sí, cada 30 días** | no | descartado |
| **duckdns** | `*.duckdns.org` | **solo a/aaaa/txt: no admite cname** | solo subdominio | no | no | descartado: no vale para un paas |
| **afraid.org** | 5 subdominios | dominios compartidos, no está en la psl | subdominio o dns | no verificado | no | descartado |
| **eu.org** | `cosknot.eu.org` | solo ns; aprobación humana de días a meses | subdominio con dns | no verificado | no | descartado para empezar |
| **deSEC / dedyn** | dns + `dedyn.io` | **registro gratis suspendido desde enero 2024** | dns o subdominio | no | no | descartado |
| **cloudflare dns** | dns + universal ssl | 200 records/zona; hay que cambiar nameservers | solo dominio propio | no | solo si compras dominio | para cuando compres dominio |
| **ngrok free** | 1 dominio estático auto-asignado | 1 gb/mes, 20k req, interstitial | subdominio | no | no | para demos rápidas |
| **quick tunnel** | `algo.trycloudflare.com` | url random en cada arranque | subdominio | n/a | no | para probar 5 min |

### is-a.dev, con la letra pequeña

- **está vivo**: último commit 2026-11-11 y unos 300 prs en los últimos 65 días (~5/día).
- **se mergea rápido**: medido sobre los últimos 300 prs cerrados → 40% de éxito, mediana 0.95 días, p90 1.62 días, máximo 7.57 días. 71 de 120 se mergearon en menos de 24 h.
- **acepta cname**, a, aaaa, txt y mx. su dns lo patrocina cloudflare y está en la public suffix list, así que cloudflare lo acepta como zona y el https universal es gratis.
- **no es tuyo**: los terms (§3 y §8) dicen "as-is", sin garantía de uptime, y pueden quitártelo "en cualquier momento, por cualquier razón, sin obligación de avisar". además, solo proyectos de desarrollo y **no comerciales**. hay un caso de revocación por abuso (issue 39749); no hay ningún caso verificado de revocación por inactividad.
- **si cosknot empieza a vender, hay que comprar dominio**. is-a.dev deja de ser válido.

### por qué is-a.dev y no otro

- **no-ip**: solo 1 hostname y te obliga a confirmar cada 30 días o deja de resolver. además no da ssl. es para una raspberry en casa.
- **duckdns**: no admite cname, así que no puedes apuntarlo a render. solo a una ip. inútil aquí.
- **eu.org**: es un dominio "de verdad" gratis, pero solo acepta ns (necesitas montar dns) y la aprobación es una lotería de días a meses. no para empezar hoy.
- **freedns.afraid.org**: dominios compartidos y fuera de la psl, cloudflare no lo acepta.
- **dedyn.io**: cerrado a registros nuevos.
- **.dev comprado**: 8.20 $ el primer año y 12.20 $/año después en cloudflare registrar; .com 11.17 $; .app 8.20 $ → 14.20 $. es lo sólido cuando haya algo que perder.

### https

- **render** emite y renueva let's encrypt para `onrender.com` y para dominios propios. es el que usamos. fuente: https://render.com/docs/custom-domains
- **let's encrypt** directo: 90 días, renovación automática, 50 certs/dominio/7 días. solo tiene sentido en una vm.
- **cloudflare universal ssl**: gratis, pero solo con el dominio en cloudflare y tráfico proxied. no aplica a is-a.dev.
- para apuntar `cosknot.is-a.dev` a render: en el json de is-a.dev, un **cname** a `cosknot.onrender.com`. render dice explícitamente que para subdominios se usa cname y para el dominio raíz una a `216.24.57.1`. **no verificado**: ningún caso real de is-a.dev + render publicado; el cname está permitido y la mecánica es la estándar.

fuentes:
- https://github.com/is-a-dev/register
- https://docs.is-a.dev/quickstart/
- https://docs.is-a.dev/faq/
- https://www.noip.com/free
- https://www.noip.com/support/knowledgebase/confirm-my-hostname-free-account-support-question-day
- https://www.duckdns.org/faqs.jsp
- https://freedns.afraid.org/signup/features/
- https://nic.eu.org/register.html
- https://talk.desec.io/t/dedyn-io-registration-suspended/1837
- https://www.cloudflare.com/plans/free/
- https://developers.cloudflare.com/ssl/edge-certificates/universal-ssl/
- https://render.com/docs/custom-domains
- https://letsencrypt.org/docs/rate-limits/
- https://ngrok.com/pricing

## 6. qué significa "añadir tarjeta pero no pagar"

- **render, neon, pythonanywhere, aiven, is-a.dev, cloudflare dns**: no piden tarjeta. riesgo de cobro: 0.
- **oracle, cloud run, azure, fly.io**: piden tarjeta (y oracle también móvil). el cargo de verificación suele ser 1 $ temporal, devuelto. el riesgo no es la verificación, es que **ninguno tiene un tope de gasto duro** que puedas activar de verdad: un error de configuración o un pico puede generar factura.
- **aws**: ya no es gratis 12 meses para cuentas nuevas; son créditos de 6 meses. y route 53 se paga.
- **recomendación**: no metas tarjeta en el mvp. no te aporta nada y añade una vía de cobro. si algún día quieres quitar el cold start, ahí sí: cloud run u oracle, asumiendo el riesgo.

## 7. coste y límites reales del mvp

| cosa | límite gratis | qué pasa al llegar |
|---|---|---|
| render web | 512 mb ram, 0.1 cpu, 5 gb banda/mes | el servicio se suspende hasta el mes siguiente |
| render sleep | 15 min sin tráfico | primer request tarda ~1 min |
| render disco | efímero | **sqlite se borra en cada deploy**. la db va en neon, no en el disco |
| render postgres | 1 gb, **caduca a los 30 días** | no usarlo |
| neon | 1 gb, 100 cu-horas/mes | se bloquean escrituras o se suspende el compute hasta el ciclo siguiente |
| is-a.dev | pull request | si no cumples las reglas o desaparece el proyecto, pierdes la url |
| imágenes | render no tiene storage | cloudflare r2 (10 gb gratis) o supabase storage cuando toque |

trampas típicas de principiante:

1. **sqlite en render**: el filesystem es efímero. la db desaparece en cada deploy. usa neon desde el principio.
2. **no hacer `pg_dump`**: neon tiene 6 h de historial, no es un backup eterno. un `pg_dump` semanal a tu pc o a r2 es gratis y te salva.
3. **keep-alive a neon**: gasta cu-horas y te suspende antes de fin de mes. no lo hagas.
4. **keep-alive a supabase**: si algún día cambias, ahí sí hace falta un `select 1` diario para que no se pause a la semana.
5. **subir `.env`**: la `DATABASE_URL` va en variables de entorno de render, nunca en el repo.

## 8. plan de despliegue (orden recomendado)

1. instalar python 3.12/3.13 en local desde python.org (no desde la microsoft store).
2. crear `requirements.txt` con `flask`, `gunicorn`, `sqlalchemy`, `psycopg[binary]` y `python-dotenv`.
3. dejar la app con `DATABASE_URL` y un `wsgi.py` que exponga `app`.
4. crear cuenta en render → new web service → conectar el repo de github.
5. build command: `pip install -r requirements.txt`; start command: `gunicorn wsgi:app`.
6. crear proyecto en neon → copiar la connection string con `-pooler` → pegarla como `DATABASE_URL` en render.
7. desplegar y probar `https://cosknot.onrender.com`.
8. opcional: fork del repo de is-a.dev, añadir `cosknot.is-a.dev` con un cname a `cosknot.onrender.com`, abrir pull request.
9. cuando lo acepten, añadir `cosknot.is-a.dev` como custom domain en render y verificar. el https se emite solo.

## 9. cuándo revisar esta decisión

- si el cold start de 1 min molesta → cloud run (tarjeta) u oracle (tarjeta + sysadmin).
- si cosknot empieza a vender → comprar `.dev` (~8-12 $/año) y revisar los terms de is-a.dev.
- si la db pasa de 1 gb o de 100 cu-horas → neon de pago (~19 $/mes) o supabase/aiven.
- si hay que guardar muchas imágenes → cloudflare r2 (10 gb gratis, egress gratis).
- si render cambia el free tier → revisar la tabla del punto 3.

## 10. qué está verificado y qué no

**verificado en fuente oficial**: precios y límites de render, cloud run, oracle, azure f1, aws, pythonanywhere, fly, vercel, netlify; límites de neon, supabase, aiven, d1, turso, cockroach, mongo, planetscale; términos de render; docs de custom domains de render; is-a.dev (repo, prs, tos); no-ip; duckdns; eu.org; cloudflare; precios de dominio.

**verificado con datos públicos**: tiempos de merge de is-a.dev (api de github sobre 300 prs); incidentes de neon/supabase/turso (status pages); cold start de cloud run (~3 s); cold start de neon (~1.1 s).

**anécdota de foro, no hecho**: suspensiones de render por tráfico saliente; db en blanco de supabase tras pausa; caídas de duckdns; cuentas cerradas de oracle; cobros de azure container apps. reddit bloquea el acceso directo, así que en varios casos solo hay título y snippet.

**no verificado**: ningún caso real de is-a.dev con cname a render funcionando; si is-a.dev tiene sla de facto (no hay status page); rangos de aprobación de eu.org; un issue concreto de neon + gunicorn; si la pérdida de datos de supabase es bug o casos aislados; free tier legacy de cockroach.
