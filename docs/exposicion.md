# exposición de cosknot

Contenido listo para exponer, ordenado como pide el enunciado. Cada sección tiene lo
que se dice y el dato que lo respalda. Los números salen del repositorio y de las
tarifas públicas de los servicios a noviembre de 2026.

Reparto del tiempo orientativo para 10 minutos:

```
equipo y roles            1 min
la idea                   2 min
rival actual              1 min
FODA                      2 min
repositorio y kanban      2 min
diseño                    1 min
CFO: dinero               1 min
CTO: tecnología           2 min
```

---

## 1. equipo y roles

Tres personas, tres responsabilidades, ninguna sin tareas.

| persona | rol | qué hace en cosknot | qué se le ve en el repositorio |
|---|---|---|---|
| Daniel Barrasa | CEO y CMO | producto, mercado, marca y comunicación | README, identidad visual, tablero, contenidos de la web |
| Jesús Larrazabal | CTO | arquitectura, código, base de datos, despliegue | `app.py`, `models.py`, `migrations/`, `Procfile`, workflows |
| Daniel Torres | CFO | ingresos, costes, comisión, punto de equilibrio | comisión en `pagos.py`, `docs/decisions/0003` |

Frase para decirlo en voz alta, y pasar rápido:

> Somos tres y nos repartimos como en una empresa pequeña de verdad: uno lleva el
> producto y la marca, otro la técnica, otro el dinero. En el tablero de GitHub cada
> tarea está asignada a uno de los tres.

---

## 2. la idea

**Problema.** Quien hace cosplay compra de tres maneras: por Instagram o Discord
hablando por privado con el creador, en marketplaces generalistas donde el cosplay se
pierde entre millones de artículos, o en tiendas de disfraces industrializados donde
todo es igual y talla única.

Ninguna de las tres resuelve lo importante: **un encargo a medida con un precio, un
plazo y una conversación ordenada**. Por privado no hay ficha, ni precio claro, ni
historial, ni forma de pagar sin dar el número de cuenta.

**Solución.** Un marketplace solo de cosplay, con cuatro especialidades: ropa, props,
pelucas y accesorios. El creador publica su obra con foto, precio y estado; el
comprador la encuentra, le escribe por el pedido y paga dentro de la web. Cosknot
cobra una comisión por la intermediación y no toca el dinero del creador más de lo que
tarda en llegar a su cuenta de Stripe.

**Usuario.** Dos, y conviene nombrarlos en la exposición:

- **Creador**: cosplayer con taller en casa, entre 18 y 35 años, que ya vende por DM y
  pierde pedidos por no tener escaparate ni cobro ordenado.
- **Comprador**: aficionado a un juego, serie o anime concreto que quiere una pieza
  fiel, no un disfraz genérico, y está dispuesto a esperar dos semanas por ella.

**Cómo se usa, en cuatro pasos.** Creador publica obra → comprador la encuentra por el
buscador → le escribe en el pedido → paga y sigue el estado del pedido. Sin correos
sueltos y sin capturas de pantalla.

**Qué está ya construido.** No es un mockup: registro con contraseñas hasheadas,
publicación con foto, buscador, pedidos con estados y mensajería, cobro con Stripe
Connect, avisos por correo, sugerencias de descripción con IA, 162 pruebas automáticas
y despliegue preparado.

---

## 3. mayor rival actual

**Etsy.** No es el único, pero es el que se lleva el cosplay que no se vende por
privado, y es contra el que hay que argumentar.

| | Etsy | cosknot |
|---|---|---|
| catálogo | todo: bisutería, muebles, cosplay | solo cosplay, cuatro especialidades |
| comisión | 6,5 % de transacción + 0,20 $ por anuncio + ~3 % de procesamiento | 8 % y nada más |
| búsqueda | el cosplay se mezcla con miles de artículos y revendedores | solo piezas de cosplay, filtradas por especialidad |
| encargo | conversación por mensajes sueltos, sin ficha ni plazo | pedido con estados, mensajería y precio cerrado |
| confianza | reputación global del vendedor | ficha de taller con especialidad y obras |
| idioma | inglés por defecto, precios en dólares | español, precios en euros |

Cómo se dice, sin descalificar al rival:

> Etsy tiene el mismo modelo que nosotros, y eso valida la idea: cobrar comisión por
> poner en contacto a quien hace y quien compra funciona. Lo que no tiene es el nicho.
> En Etsy una peluca de cosplay compite en la misma búsqueda que un collar de ganchillo,
> y eso hace que el comprador no encuentre lo que busca y el creador no destaque.

**Competencia secundaria**, por si preguntan:

| rival | qué le gana | qué le falta |
|---|---|---|
| AliExpress y tiendas de disfraces | precio y envío rápido | nada a medida, calidad industrial |
| Instagram, TikTok y Discord | es donde ya están los creadores | sin escaparate, sin precio, sin cobro |
| Vinted y Wallapop | confianza y volumen | segunda mano, no encargo nuevo |

---

## 4. matriz FODA

```
                 INTERNO                              EXTERNO
        ┌────────────────────────────────┬────────────────────────────────┐
  +     │ FORTALEZAS                     │ OPORTUNIDADES                  │
        │ · nicho concreto: solo cosplay │ · comunidades hispanas activas │
        │ · comisión 8 % frente al 10 % │ · salones y eventos como canal │
        │   real de Etsy                 │ · creadores que ya venden por  │
        │ · pedido con estados y         │   DM y no tienen escaparate    │
        │   mensajería, no un chat       │ · hueco en español: Etsy está  │
        │ · coste de infraestructura 0 € │   en inglés y en dólares       │
        │ · equipo que conoce el hobby   │ · temporadas: cada salón mueve │
        │ · código propio y adaptable    │   encargos con meses de margen│
        ├────────────────────────────────┼────────────────────────────────┤
  -     │ DEBILIDADES                    │ AMENAZAS                       │
        │ · marca desconocida, 0 usuarios│ · Etsy y AliExpress por precio │
        │ · catálogo de ejemplo, no real │ · Instagram como canal de compra│
        │ · sin valoraciones todavía     │ · comisión de Stripe se come   │
        │ · un solo servidor: si cae,    │   margen en pedidos pequeños   │
        │   cae la web                   │ · propiedad intelectual de los │
        │ · el creador debe conectar     │   personajes (zona gris legal) │
        │   Stripe para cobrar           │ · dependencia del crédito de   │
        │ · sin app móvil                │   estudiante para el hosting   │
        └────────────────────────────────┴────────────────────────────────┘
```

**Las dos que hay que defender con datos**, porque son las que van a preguntar:

*Debilidad: cero usuarios.* Se responde con el plan, no con optimismo: el lanzamiento
es por comunidades concretas (Discord de cosplay en español, salones), no abierto al
público, y las primeras 20 fichas se captan a mano hablando con creadores.

*Amenaza: la comisión de Stripe.* En un pedido de 10 €, Stripe se lleva 0,40 € (1,5 % +
0,25 €) y nuestra comisión son 0,80 €. En pedidos por debajo de ~5 € el modelo no
tiene sentido, y por eso el precio mínimo de una obra no es una decisión estética: es
una decisión de margen.

---

## 5. repositorio y tablero

**Repositorio:** `github.com/Barbarno/Cosknot`, público, con `README.md` que explica
qué es el proyecto, quién lo lleva y qué hay hecho.

**Tablero:** un GitHub Project con cuatro columnas: *Por hacer*, *En curso*, *Hecho*,
*Aprobado*. Todos los ítems son issues del repositorio, de modo que una tarea y su
conversación viven en el mismo sitio.

Regla que se enseña en la exposición: **las tareas no se borran, se mueven a la
derecha.** Una tarea que ya no aplica se queda en *Hecho* con el motivo escrito, para
que se vea el trabajo y no solo el resultado.

### tareas del tablero, por rol

**CEO — producto, marca, mercado, comunicación**

| tarea | columna |
|---|---|
| definir el primer usuario y el problema | Hecho |
| escribir el posicionamiento del producto | Hecho |
| crear el brief de identidad visual | Hecho |
| redactar el README del repositorio | Hecho |
| montar el tablero con sus cuatro columnas | Hecho |
| escribir la página de equipo (`/nosotros`) | Hecho |
| preparar el guion de la exposición | En curso |
| abrir las cuentas de los servicios y documentar accesos | Hecho |
| plan de lanzamiento en comunidades y salones | Por hacer |

**CTO — técnica**

| tarea | columna |
|---|---|
| elegir la arquitectura técnica inicial | Hecho |
| definir el modelo de datos inicial | Hecho |
| construir la portada y el listado de creadores | Hecho |
| diseñar el flujo de descubrimiento de creadores | Hecho |
| diseñar el perfil de creador y la ficha de obra | Hecho |
| implementar registro, entrada y perfil | Hecho |
| implementar publicación de obras con subida de foto | Hecho |
| implementar pedidos, estados y mensajería | Hecho |
| integrar el cobro con Stripe Connect | Hecho |
| implementar la cola de reintentos de correo | Hecho |
| añadir sugerencias de descripción con Gemini | Hecho |
| escribir las 162 pruebas automáticas | Hecho |
| definir las reglas de seguridad y contenido | Hecho |
| preparar el despliegue en Heroku y las copias de seguridad | En curso |
| conectar el dominio y verificar el correo | Hecho |

**CFO — dinero**

| tarea | columna |
|---|---|
| investigar el modelo de negocio | Hecho |
| calcular el coste de infraestructura y compararlo con alternativas | Hecho |
| fijar la comisión y calcular el punto de equilibrio | Hecho |
| documentar los seis riesgos del plan de hosting | Hecho |
| presupuesto de lanzamiento y renovación del dominio | Por hacer |

**Los tres**

| tarea | columna |
|---|---|
| elegir el nombre y validar el dominio | Hecho |
| revisar el diseño antes de publicar | Aprobado |
| aprobar el contenido de la exposición | Por hacer |

En pantalla se enseña el tablero y se señala una cosa: **cada tarjeta tiene una persona
asignada y ninguna persona está sin tarjetas.** Es el criterio que pide el enunciado y
se ve de un vistazo en la columna de avatares.

---

## 6. diseño

**Nombre: cosknot.** De *cos* (cosplay) y *knot* (nudo). Un nudo es lo que se hace al
terminar una costura, y también lo que ata a un creador con su comprador. Dos sílabas,
se lee igual en español y en inglés, sin guion, sin número, sin tilde, y el dominio
`cosknot.me` estaba libre. Un nombre que hay que explicar es un nombre malo; este se
entiende al verlo escrito.

**Eslogan: «cosplay, pieza a pieza».** Dice las dos cosas: qué se vende y cómo se hace,
a mano y por partes. Alternativa para cartelería corta: «tu personaje, pieza a pieza».

**Logo.** Dos ficheros SVG escritos a mano, menos de 2 KB entre los dos, escalan sin
perderse:

- `static/img/logo.svg`: la marca más la palabra «Cosknot», para cabecera, pie y correo.
- `static/img/logo-mark.svg`: solo la marca en cuadrado, para favicon, avatar y redes.

Qué es: una **C** negra sobre un cuadrado salmón, atravesada por una **aguja** con su
**hilo** en crema, y el hilo sale suelto hacia la derecha hasta enlazar con las letras.
La C es cosknot, la aguja es el oficio, el hilo es la unión entre creador y comprador.

**Tipografía.** Dos, y ninguna se descarga:

| uso | tipografía | por qué |
|---|---|---|
| logotipo | Arial Black, peso 900, interletra −3,4 | letra gruesa que aguanta tamaño pequeño |
| texto e interfaz | Segoe UI con reserva en system-ui, Arial | la del sistema: cero descargas, cero parpadeo, se ve nativa en cada dispositivo |

**Colores.** Tres papeles, con el acento llamativo y el resto mate:

| papel | color | hex | dónde |
|---|---|---|---|
| primario (mate) | crema cálido | `#f7f1e8` | fondos amplios, cabecera |
| primario (mate) | gris superficie | `#f5f5f5` | tarjetas y secciones |
| secundario (mate) | grafito | `#222222` | texto, bordes, logotipo |
| secundario (mate) | gris tinta | `#595959` | texto secundario |
| **acento (llamativo)** | **salmón** | `#fa8072` | botones, precios, marca |
| acento profundo | salmón quemado | `#b8443a` | enlaces y hover |
| acento suave | salmón claro | `#fde3de` | etiquetas y avisos |

Degradado de acento, para cabeceras y botones destacados:

```css
background: linear-gradient(135deg, #fa8072 0%, #b8443a 100%);
```

El criterio, en una frase: **el fondo no compite y el salmón sí.** Todo lo que el
usuario tiene que pulsar es salmón; todo lo demás es crema, gris o grafito. Nunca hay
dos acentos en la misma pantalla.

---

## 7. CFO: ingresos, costes y punto de equilibrio

### ingresos

**Modelo: comisión por venta.** No hay suscripción ni anuncios. Se cobra un **8 %** del
importe del pedido en el momento del pago; el 92 % restante va a la cuenta de Stripe del
creador. La comisión es una variable de entorno (`COMMISSION_PERCENT`), así que se puede
cambiar sin tocar código, y sin ella el cobro se apaga en vez de cobrar mal.

Por qué comisión y no suscripción: un creador que empieza no paga 10 €/mes por algo que
todavía no le trae ventas. La comisión solo se cobra cuando hay dinero, y eso es lo que
hace que se registre.

Por qué no anuncios: con el tráfico de un proyecto de clase, la publicidad daría
céntimos y ensuciaría una web cuyo valor es la confianza en el escaparate.

Ingresos adicionales previstos, no implementados: destacar una obra en portada durante
una semana, y un plan de taller verificado con más fotos.

### costes

**Inversión inicial: 0 €.** El dominio del primer año sale del GitHub Student Pack, todo
el software es libre, y la infraestructura arranca con capas gratuitas. El trabajo es
del equipo.

**Mantenimiento mensual**, con precios reales:

| concepto | coste | cubierto por |
|---|---|---|
| Heroku dyno Basic | 7 $/mes | crédito de estudiante |
| Heroku Postgres Essential-0 | 5 $/mes | crédito de estudiante |
| dominio `cosknot.me` | 0 € el primer año | cupón del pack |
| Cloudflare DNS | 0 € | plan Free |
| Resend (correo) | 0 € hasta 3.000/mes | plan Free |
| Cloudflare R2 (fotos) | 0 € hasta 10 GB | plan Free |
| GitHub Actions | 0 € en repo público | plan Free |
| Stripe | 1,5 % + 0,25 € por cobro | lo paga el creador en cada venta |
| **total** | **12 $/mes ≈ 11,10 €** | **0 € de caja hasta noviembre de 2028** |

El crédito son **312 $** (13 $/mes durante 24 meses). A 12 $/mes cubre **26 meses**.
Después de eso, el coste real es 12 $/mes más unos 12 €/año de dominio.

### punto de equilibrio

Con el crédito activo, el punto de equilibrio es **0 pedidos**: el proyecto no cuesta
dinero. Ese es el escenario de la exposición, y hay que decirlo así de claro.

El cálculo interesante es el de después del crédito, cuando la infraestructura se paga
sola:

```
coste fijo mensual        12,10 €  (11,10 € de Heroku + 1,00 € de dominio al año)
comisión por pedido        8 % del importe
pedido medio              45 €
ingreso por pedido        3,60 €

punto de equilibrio       12,10 ÷ 3,60 = 3,36  →  4 pedidos al mes
```

**Cuatro pedidos al mes** cubren toda la infraestructura. Y la sensibilidad, que es lo
que suele preguntar el tribunal:

| pedido medio | ingreso por pedido | pedidos/mes para equilibrio |
|---|---|---|
| 15 € | 1,20 € | 11 |
| 25 € | 2,00 € | 7 |
| 45 € | 3,60 € | 4 |
| 80 € | 6,40 € | 2 |

Conclusión honesta para decir en voz alta:

> Este proyecto no está pensado para ganar dinero, está pensado para demostrar que el
> modelo funciona. Y funciona con muy poco: cuatro encargos al mes de 45 € ya pagan el
> servidor, el dominio y la base de datos. El riesgo no es el margen, es conseguir esos
> cuatro encargos.

---

## 8. CTO: necesidades tecnológicas

### qué necesita el proyecto

| necesidad | solución elegida | por qué |
|---|---|---|
| servir páginas web | Flask 3.1.3 sobre Python 3.13 | microframework: se ve cada pieza y se explica en clase |
| base de datos | PostgreSQL 16 en Heroku; SQLite en local | el mismo SQL en los dos, y en local arranca sin instalar nada |
| acceso a datos | SQLAlchemy 2.1.8 | evita SQL a mano y bloquea la inyección por construcción |
| cambios de esquema | Alembic 1.20.1, 7 migraciones | cada cambio de tablas queda versionado y reversible |
| plantillas HTML | Jinja2 | renderizado en servidor, sin compilación de frontend |
| estilos | CSS propio, 32 KB | sin Bootstrap ni Tailwind: control total y cero dependencias |
| sesiones y seguridad | Flask-Login, Flask-WTF, Argon2id, Flask-Limiter | sesión, CSRF, hash de contraseñas y límite de intentos |
| fotos | Cloudflare R2 (S3 compatible) con boto3 | 10 GB gratis y sin servidor que mantener |
| correo | Resend con cola de reintentos propia | si el correo falla, el aviso no se pierde |
| cobros | Stripe Connect | el dinero va directo al creador, no pasa por nosotros |
| IA | Google Gemini | sugerir la descripción de una obra, a petición del usuario |
| errores en producción | Sentry | entero y con traza, sin revisar logs a mano |
| despliegue | Heroku + gunicorn, 1 worker y 4 hilos | el plan mínimo y el límite de conexiones manda |
| integración continua | GitHub Actions, 162 pruebas | nada llega a main sin pasar las pruebas |
| copias de seguridad | `pg_dump` diario, cifrado, a R2, purga a 30 días | la base se puede reconstruir |

### por qué estas y no otras

**Flask y no Django.** Django trae administrador, ORM y autenticación hechos. Para
aprender, eso esconde justo lo que hay que explicar: cómo se hashea una contraseña, cómo
se protege un formulario, cómo se modela un pedido. Con Flask cada pieza está escrita y
se puede señalar en la exposición.

**PostgreSQL y no MongoDB.** El dominio es relacional por todas partes: un usuario tiene
un taller, un taller tiene obras, una obra acaba en pedidos, un pedido tiene mensajes.
Eso son claves foráneas, no documentos sueltos.

**Sin React ni Vue.** La web se renderiza en el servidor y tiene cuatro interacciones.
Un framework de frontend añadiría una compilación, un `node_modules` y un segundo
lenguaje, sin nada a cambio.

**Un solo worker en gunicorn.** Está razonado en el `Procfile`, no copiado: el límite de
intentos vive en memoria del proceso, así que con dos workers cada uno llevaría su propia
cuenta y el cupo real sería el doble. Y 512 MB de RAM son el recurso escaso del plan.

### dónde se despliega

```
aplicación   Heroku, dyno Basic, región Europa
base         Heroku Postgres Essential-0, 1 GB y 20 conexiones
DNS          Cloudflare, plan Free, en gris (sin proxy)
dominio      cosknot.me, gratis el primer año por el pack de estudiante
HTTPS        certificado automático de Heroku
correo       Resend, dominio verificado con DKIM, SPF y DMARC
```

El detalle que se puede lucir: **Cloudflare va en gris a propósito.** Con el proxy
naranja habría dos saltos y el certificado de Heroku fallaría la validación HTTP-01;
además el limitador de intentos contaría la IP de Cloudflare en lugar de la del
visitante.

### riesgos técnicos, ya asumidos

| riesgo | consecuencia | mitigación |
|---|---|---|
| un solo dyno | si cae, la web cae | `/healthz` con aviso diario por workflow |
| contador de intentos en memoria | se reinicia al reiniciar el dyno | aceptable con un worker |
| 20 conexiones de PostgreSQL | el pool se queda en 3 + 2 | configuración por variable de entorno |
| 512 MB de RAM | sin margen para procesos pesados | un worker, fotos fuera del servidor |
| arranque en frío tras desplegar | unos segundos de espera | aceptable en un proyecto |
| crédito temporal | en noviembre de 2028 deja de cubrir | decisión documentada y alternativa gratuita lista |

---

## 9. qué enseñar en pantalla, en este orden

1. **El repositorio**, con el `README` arriba: qué es, quién lo lleva, qué hay hecho.
2. **El tablero**, señalando que hay cuatro columnas y que cada tarjeta tiene dueño.
3. **La web**: portada → filtro por especialidad → ficha de obra → buscador.
4. **Un pedido**: cómo se escribe al creador y cómo cambia de estado.
5. **Un detalle técnico**: `/healthz` respondiendo, o las 162 pruebas pasando en verde.

Con la web delante, tres frases que cierran bien:

> Esto no es una maqueta: el registro hashea contraseñas con Argon2id, los formularios
> llevan token CSRF, hay límite de intentos por IP y el cobro está integrado con Stripe.
>
> Y arranca sin ninguna clave: si falta el servicio de correo, los avisos se quedan en
> cola en vez de romper la web.
>
> Todo lo que veis corre en servicios gratuitos o cubiertos por el pack de estudiante:
> el coste del proyecto hasta la entrega es cero.
