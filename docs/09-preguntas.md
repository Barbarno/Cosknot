# qué hace cada pieza y qué contestar si preguntan

Anexo de [`08-cto.md`](08-cto.md). Aquí no se decide nada: se explica lo que ya está
decidido, en una línea por tecnología, y se contestan las preguntas que suelen caer.

## qué hace cada una, en una línea

| pieza | qué es | qué hace en cosknot |
|---|---|---|
| **Python** | lenguaje de programación | se escribe todo: la web, los scripts y las pruebas |
| **Flask** | framework web | recibe cada dirección (`/creadores`, `/obras/...`), ejecuta el código y devuelve la página |
| **Jinja2** | motor de plantillas | convierte una plantilla con huecos en HTML relleno con los datos del taller |
| **PostgreSQL** | base de datos relacional | guarda usuarios, talleres, piezas, pedidos y mensajes, con relaciones entre ellos |
| **SQLite** | base de datos de un solo fichero | la misma base en local, sin instalar nada |
| **SQLAlchemy** | ORM | escribe el SQL por nosotros y evita la inyección por construcción |
| **Alembic** | migraciones | cada cambio de tablas queda como un paso numerado y reversible |
| **gunicorn** | servidor de aplicación | mantiene la web viva y reparte las peticiones entre hilos |
| **Cloud Run** | plataforma de ejecución | ejecuta la web con URL y HTTPS; arranca instancias si hay visitas y las apaga si no |
| **Cloud Run Jobs** | tareas puntuales | aplica las migraciones y vacía la cola de correos sin tener un proceso encendido |
| **Cloud Scheduler** | reloj de tareas | lanza el vaciado de la cola cada minuto |
| **Neon** | PostgreSQL gestionado | guarda los datos en producción con copias y parches incluidos |
| **certificado de Cloud Run** | HTTPS | emite y renueva el certificado del dominio, gratis y sin tocar nada |
| **Cloudflare** | DNS y CDN | traduce `cosknot.me` a la dirección del servidor |
| **Cloudflare R2** | almacenamiento de objetos | guarda las fotos fuera del servidor, que es efímero y no está para eso |
| **Stripe** | pasarela de pago | cobra con tarjeta sin que los datos del comprador pasen por nosotros |
| **Stripe Connect** | cuentas de cobro | cada taller cobra en su cuenta; nosotros retenemos la comisión |
| **Resend** | correo transaccional | manda los avisos de pedido y no acaban en spam |
| **Gemini** | modelo de IA | propone título y descripción a partir de la foto, si el usuario lo pide |
| **Sentry** | vigilancia de errores | avisa cuando algo falla en producción, con la traza exacta |
| **GitHub Actions** | integración continua | ejecuta las pruebas en cada subida y bloquea lo que rompe |
| **pytest** | marco de pruebas | comprueba que la web sigue funcionando tras cada cambio |

## diccionario mínimo

| palabra | qué significa, sin rodeos |
|---|---|
| **framework** | un esqueleto de programa que ya trae lo repetitivo hecho; uno rellena lo suyo |
| **ORM** | capa que traduce clases de Python a tablas de SQL, y al revés |
| **migración** | fichero que dice «añade esta columna»; se aplica en orden y se puede deshacer |
| **variable de entorno** | valor que se pasa al programa desde fuera del código, para no escribir claves dentro |
| **API** | la puerta que un servicio abre para que otro programa le pida cosas |
| **webhook** | aviso que un servicio manda a tu web cuando pasa algo («este pago se ha completado») |
| **HTTPS / TLS** | la web cifrada; el candado del navegador |
| **certificado** | el documento que demuestra que ese dominio es de verdad ese servidor |
| **DNS** | la guía de teléfonos de internet: nombre → dirección |
| **CDN** | copia de los ficheros cerca del visitante para que carguen rápido |
| **pool de conexiones** | número máximo de conversaciones a la vez con la base de datos |
| **worker** | proceso que atiende peticiones dentro de una instancia; más workers, más capacidad |
| **instancia** | una copia del programa en marcha; Cloud Run puede tener cero, dos o veinte |
| **escala automática** | que el número de instancias suba y baje solo según las visitas |
| **arranque en frío** | el retraso de la primera visita después de un rato sin tráfico: 1–3 s |
| **pooler** | intermediario que reparte conexiones a la base para no abrir cien a la vez |
| **renderizado en servidor** | el HTML se monta en el servidor y llega hecho, no se monta en el navegador |
| **CI** | que cada subida de código se pruebe sola antes de darla por buena |

## si preguntan

**¿Por qué Flask y no Django?**
Django trae administrador, ORM y login hechos: para aprender esconde justo lo que hay
que explicar. Con Flask cada pieza está escrita y se puede señalar.

**¿Por qué PostgreSQL y no MongoDB?**
Porque el dominio es relacional: un usuario tiene un taller, un taller tiene piezas, una
pieza acaba en pedidos, un pedido tiene mensajes. Eso son claves foráneas, no documentos
sueltos.

**¿Por qué dos bases de datos?**
No son dos: es la misma tecnología con dos motores. En local, SQLite (un fichero, cero
instalación); en producción, PostgreSQL (varios usuarios a la vez). El SQL es el mismo.

**¿Qué es un ORM y para qué sirve?**
Escribir `sesion.get(Work, 3)` en vez de `SELECT * FROM works WHERE id = 3`. Además
escapa los valores, así que una comilla en el buscador no puede inyectar SQL.

**¿Por qué Alembic si puedo cambiar la tabla a mano?**
Porque a mano hay que acordarse de hacer lo mismo en producción, y no queda registro.
Con Alembic el cambio está en el repositorio, se aplica solo al desplegar y se puede
deshacer.

**¿Por qué gunicorn y no el servidor de desarrollo de Flask?**
El de Flask es de un solo hilo y avisa de que no vale para producción. gunicorn atiende
varias peticiones a la vez y se reinicia si se cae.

**¿Por qué dos workers y varias instancias?**
Antes de Cloud Run esto era un problema: el límite de intentos por IP vivía en la memoria
del proceso, así que con dos workers cada uno llevaba su cuenta y el cupo real se
duplicaba. Ahora el contador es una **tabla en la base de datos**, y da igual cuántas
instancias haya: el cupo es el mismo. Con eso resuelto, se puede escalar sin abrir un
agujero en el inicio de sesión.

**¿Qué es una instancia?**
Una copia del programa en marcha, con su memoria y su proceso. Cloud Run las crea cuando
llegan visitas y las destruye cuando dejan de llegar. No hay un servidor fijo con nombre.

**¿Qué pasa si mañana hay 100 clientes?**
Nada especial, y esa es la razón de haberlo elegido. Cloud Run levanta más instancias si
hace falta (hasta el máximo que se configure) y el tramo gratuito —2 millones de
peticiones al mes— está cien veces por encima de lo que genera un marketplace con 100
talleres. Las fotos ya están en R2 y la base en Neon, así que ninguna de las dos depende
del número de instancias.

**¿Y el arranque en frío?**
La primera visita después de un rato sin nadie tarda 1–3 segundos, porque hay que levantar
una instancia desde cero. Después responde en milisegundos. Se puede quitar dejando una
instancia mínima encendida, y eso cuesta unos euros al mes; se ha decidido no pagarlo.

**¿Qué es Cloud Run y por qué no un servidor normal?**
Es la plataforma de Google que ejecuta el programa en una imagen construida desde el
repositorio. La diferencia con un servidor normal es que **no hay máquina que administrar**:
sin sistema operativo que parchear, sin certificado que renovar y sin copias que programar
—eso último lo cubre Neon—. Y con un servidor normal, el día que no hay visitas sigues
pagándolo; aquí no.

**¿Por qué Neon y no el PostgreSQL de Google?**
Porque Cloud SQL, el de Google, es de pago desde el primer día y no tiene plan gratuito.
Neon da PostgreSQL 16 con copias y un *pooler*, y 0,5 GB gratis, que es veinte veces lo
que ocupa este proyecto. El código no cambia: lo único distinto es la cadena de conexión.

**¿Quién pone el certificado HTTPS?**
Cloud Run, automáticamente, cuando el dominio apunta al servicio. Lo emite, lo instala y lo
renueva sin que nadie toque nada. Cloudflare se queda en «solo DNS» (nube gris) para no
meter un segundo proxy en medio.

**¿Por qué Cloudflare en gris y no en naranja?**
Porque en naranja Cloudflare se pone delante y todas las peticiones llegan con **su** IP, no
con la del visitante: el límite de intentos por IP dejaría de proteger nada y contaría a
todo el mundo como una sola persona. En gris, el DNS apunta directo al servicio y la IP que
llega es la real. El certificado lo pone Cloud Run, así que tampoco se gana nada con el
proxy.

**¿Stripe se queda con el dinero?**
No. Con Connect, el cobro va a la cuenta del creador y la plataforma retiene solo su
comisión. Nosotros nunca tocamos el dinero del taller.

**¿Por qué no cobrar nosotros y repartir después?**
Porque eso obliga a custodiar dinero de terceros, con obligaciones legales y contables.
Connect lo evita: el dinero nunca pasa por nuestra cuenta.

**¿Qué pasa si Stripe no está configurado?**
La web arranca igual: el botón de pagar no aparece y se explica el motivo. Es una regla
de diseño: ninguna clave ausente rompe el sitio.

**¿Qué es R2 y por qué no guardar las fotos en el servidor?**
R2 es almacenamiento de objetos compatible con S3. En Cloud Run el disco es efímero: cada
instancia nace vacía y muere cuando se apaga, así que una foto subida al servidor
desaparecería. En R2 hay 10 GB gratis y las fotos se sirven desde la CDN.

**¿Y si se cae Cloud Run?**
Google reparte las instancias entre varias máquinas, así que la caída de una no tira la
web: la sustituye. Lo que sí es un punto único es el proveedor: si Cloud Run entero falla,
la web no responde. Se asume, con un `/healthz` que comprueba servicio y base, y un aviso
diario por GitHub Actions. La salida está preparada: el mismo código en Heroku, con el
crédito de 312 $.

**¿Y si Google cambia el tramo gratuito?**
Se paga, o se muda. Las dos cosas son baratas porque el código no depende de Google: no hay
nada específico de Cloud Run salvo escuchar en `$PORT` y un comando de arranque. Mudarse a
Heroku es un `git push` y 12 $/mes cubiertos por el crédito. Eso es exactamente lo que
comprueba que la elección de hosting es reversible.

**¿Cómo guardáis las contraseñas?**
Nunca en claro: se guarda un hash con Argon2id y una sal por usuario. Ni nosotros podemos
leerlas.

**¿Qué es CSRF?**
Un ataque que hace que tu navegador envíe un formulario sin que quieras. Se evita con un
token que solo tiene la página original.

**¿Por qué no React o Vue?**
Porque la web se renderiza en el servidor y tiene dos interacciones. Un framework de
frontend añadiría compilación, `node_modules` y un segundo lenguaje, sin nada a cambio.

**¿Por qué no Docker o Kubernetes?**
Porque no hacen falta. Cloud Run construye la imagen él solo a partir de `requirements.txt`
y un comando de arranque: se sube el código y ya. Un `Dockerfile` sería una capa más que
mantener y explicar sin resolver nada que no esté resuelto, y Kubernetes es para orquestar
decenas de servicios, no uno. Si algún día hace falta control total de la imagen, se añade
en una tarde y la plataforma lo acepta.

**¿Por qué no Oracle Cloud si da 24 GB gratis?**
Se evaluó. Da más máquina y no caduca, pero hay que administrar el sistema operativo, el
certificado y las copias, y la instancia ARM gratuita no siempre está disponible. Con 100
clientes Cloud Run ya cubre el requisito sin administrar nada y sin coste. Está comparado
por escrito en [`08-cto.md`](08-cto.md#por-qué-estas-y-no-otras).

**¿Cuánto cuesta todo esto?**
**0 €/mes.** Cloud Run y Neon están dentro del tramo gratuito con muchísimo margen (2
millones de peticiones y 0,5 GB frente a las ~20.000 peticiones y ~50 MB de 100 talleres),
y el dominio es gratis el primer año con el pack de estudiante. A partir del segundo año
solo se paga el dominio, unos 12 €/año. Los 312 $ del pack de estudiante siguen intactos y
sirven de red si algún día hay que pagar infraestructura. Stripe y Resend cobran por uso;
con poco volumen, céntimos.

**¿Se puede cambiar de tecnología más adelante?**
Sí, y se ha elegido sabiendo eso. Cambiar de hosting son horas; cambiar de base de datos
es un fin de semana; cambiar de framework es reescribir la web. Por eso las dos primeras
se eligen baratas de cambiar y la tercera se elige una vez.

**¿Qué NO vais a usar?**
React, Kubernetes, MongoDB, Redis, app móvil, Docker y un servidor propio (Oracle o
cualquier otra máquina virtual). Ninguna resuelve un problema que tengamos hoy; todas se
pueden añadir después, y las dos últimas están comparadas por escrito para que se vea que
se miraron.
