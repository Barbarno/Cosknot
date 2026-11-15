# tablero kanban

Tablero real: **`Kanban-Cosknot`** en GitHub Projects, enlazado al repositorio
`Barbarno/Cosknot`. Cada tarjeta es un issue del repositorio, así que se puede abrir y
leer dentro la decisión que la cierra.

```
┌──────────────────┬──────────────────┬──────────────────┬──────────────────┐
│ TO DO            │ DOING            │ DONE             │ APPROVED         │
│ trabajo futuro   │ en lo que se     │ entregable que   │ decisión tomada  │
│                  │ está ahora       │ ya se puede abrir│ y escrita        │
└──────────────────┴──────────────────┴──────────────────┴──────────────────┘
```

Cinco reglas, y las cinco se ven en la exposición:

1. **Las columnas son esas cuatro**, ni una más.
2. **Todas las tareas están escritas.** Si no está en el tablero, no existe.
3. **Las tareas no se borran.** Lo que ya no aplica se queda en *Done* con el motivo.
4. **Cada tarea tiene una persona.** Ni una tarjeta sin dueño.
5. **Nada que no esté hecho se marca como hecho.** En esta entrega se eligen las
   tecnologías, no se demuestran: lo que implica ejecutar o verificar está en *Doing*,
   nunca en *Approved*.

## CEO · Daniel Barrasa — producto, marca, diseño y comunicación

| # | tarea | columna |
|---|---|---|
| 21 | Eslogan cosknot | approved |
| 22 | Logo cosknot | approved |
| 25 | Búsqueda de colores cosknot | approved |
| 26 | Búsqueda de tipografía cosknot | approved |
| 27 | Búsqueda de nombre y dominio | approved |
| 30 | Mayor rival actual | approved |
| 31 | Matriz FODA | approved |
| 28 | `README` del repositorio | done |
| 29 | Tablero kanban con cuatro columnas | done |
| 40 | Guion de la exposición | doing |
| 49 | Alta de los primeros 20 talleres | to do |
| 50 | Plan de lanzamiento en Discord y salones | to do |

## CTO · Jesús Larrazabal — tecnologías, base de datos y despliegue

| # | tarea | columna |
|---|---|---|
| 18 | Búsqueda de bbdd | approved |
| 19 | Lenguajes de programación | approved |
| 20 | Creación de bases de datos | approved |
| 23 | Dónde desplegar la aplicación | approved |
| 32 | Búsqueda de IA para las fichas | approved |
| 33 | Búsqueda de servicios de apoyo | approved |
| 24 | Alteración de cuentas para Heroku → Cloud Run | doing |
| 34 | Documento de despliegue en Cloud Run | doing |
| 39 | Configurar el proyecto de Google Cloud | doing |
| 42 | Crear el proyecto en Neon y guardar la cadena | doing |
| 43 | Desplegar en Cloud Run y comprobar `/healthz` | doing |
| 44 | Mapear `cosknot.me` en Cloudflare | doing |
| 45 | Prototipo de portada y listado | to do |
| 46 | Prototipo de la ficha de una pieza | to do |
| 47 | Integrar el cobro con Stripe Connect | to do |
| 48 | Montar la integración continua | to do |

## CFO · Daniel Torres — ingresos, costes y punto de equilibrio

| # | tarea | columna |
|---|---|---|
| 35 | Búsqueda del modelo de ingresos | approved |
| 36 | Búsqueda de costes iniciales y de mantenimiento | approved |
| 37 | Cálculo del punto de equilibrio | approved |
| 38 | Precio del plan premium del taller | approved |
| 41 | Margen por pedido con las tarifas de Stripe | doing |
| 51 | Techo de gasto de la infraestructura | to do |
| 52 | Presupuesto del dominio para el segundo año | to do |

## qué hay escrito dentro de cada tarjeta aprobada

La gracia del tablero es que la decisión está en el issue, no solo en el título:

| tarjeta | lo que se decidió |
|---|---|
| 25 · colores | crema `#f7f1e8` y gris `#f5f5f5` mates, grafito `#222222`, acento salmón `#fa8072` |
| 26 · tipografía | Etna Sans Serif en el logotipo (a trazados) y Segoe UI en el texto |
| 27 · nombre | `cosknot` con dominio `cosknot.me`, gratis el primer año |
| 30 · rival | Etsy: ~10 % de comisión, catálogo abierto, inglés · cosknot: 8 %, solo cosplay, español |
| 31 · FODA | fortalezas, oportunidades, debilidades y amenazas, tres palabras cada una |
| 19 · lenguajes | Python 3.13 + Flask 3 + Jinja2, sin framework de frontend |
| 20 · base de datos | PostgreSQL 16 en Neon (0,5 GB), SQLite en local |
| 23 · despliegue | Google Cloud Run; descartados Oracle, Render, Fly y Cloud SQL |
| 32 · IA | Google Gemini, opcional: sin clave el botón no aparece |
| 33 · servicios | Resend, Cloudflare R2, Stripe Connect y Cloudflare DNS |
| 35 · ingresos | comisión del 8 %; suscripción y anuncios descartados como fuente principal |
| 36 · costes | 0 € inicial y 0 €/mes; dominio ~12 €/año desde el segundo año |
| 37 · equilibrio | 1 pedido/mes (4 si algún día se pagara toda la infraestructura) |

## por qué *Doing* y no *Done* en el despliegue

La tarjeta 34 tiene un documento escrito, y aun así no está terminada: **no hay nada
desplegado**. `gcloud` no está instalado, no hay cuentas creadas y las cifras de coste son
las que publica Google, no una medición. Ponerla en *Done* sería afirmar que el sistema
está en producción, y no lo está.

Lo mismo con la 24: el código está adaptado y las pruebas pasan, pero eso es trabajo en
curso, no un despliegue terminado.

En la exposición la frase es una: «las tecnologías están elegidas y justificadas; el
despliegue está documentado y pendiente». Ninguna tarjeta del tablero promete lo contrario.

## del enunciado al tablero

| lo que pide el enunciado | tarjeta | documento |
|---|---|---|
| repositorio con `README.md` | 28 | `README.md` |
| project con cuatro columnas | 29 | este documento |
| todas las tareas escritas y sin borrar | 18–52 | este documento |
| tareas asignadas por rol, nadie sin tareas | todas | `docs/01-equipo.md` |
| nombre, logo, eslogan, tipografía y colores | 21, 22, 25, 26, 27 | `docs/06-diseno.md` |
| mayor rival actual | 30 | `docs/03-rival.md` |
| matriz FODA | 31 | `docs/04-foda.md` |
| CFO: ingresos, costes y punto de equilibrio | 35, 36, 37, 38 | `docs/07-cfo.md` |
| CTO: necesidades, lenguajes, bases de datos y despliegue | 18, 19, 20, 23 | `docs/08-cto.md` |

## tareas descartadas, y por qué siguen en el tablero

La regla de no borrar se demuestra aquí: lo que se cayó se queda con el motivo escrito
dentro del issue.

| decisión descartada | motivo |
|---|---|
| desplegar en Heroku con el crédito del pack | se cambia a Cloud Run + Neon: 0 €/mes, escala de 0 a 4 instancias y no hay servidor que administrar |
| Oracle Cloud Always Free | 24 GB de RAM que no se usan y una máquina que administrar |
| app móvil en la primera entrega | la web cubre el encargo con fotos y pago; la app es fase dos |
| Redis para el contador de intentos | un proveedor más por 80 líneas de código; se resuelve con la tabla `intentos` |

## recuento

| columna | tarjetas |
|---|---|
| approved | 17 |
| doing | 8 |
| done | 2 |
| to do | 8 |
| **total** | **35**, todas con persona |

## cómo se lee en pantalla

Se abre el tablero y se señalan tres cosas: **cuatro columnas**, **una persona en cada
tarjeta** y **ninguna tarjeta sin dueño**. Después se abre una cualquiera —la 25, los
colores— y se ve la decisión escrita dentro. Eso es lo que separa un tablero de una lista
de deseos.
