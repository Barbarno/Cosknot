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
| **Heroku** | hosting | ejecuta el programa en un servidor con URL y HTTPS; no administramos la máquina |
| **Let's Encrypt** | autoridad de certificados | emite el certificado que hace que la web sea `https://` y gratis |
| **Cloudflare** | DNS y CDN | traduce `cosknot.me` a la dirección del servidor |
| **Cloudflare R2** | almacenamiento de objetos | guarda las fotos fuera del servidor, que solo tiene 512 MB |
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
| **worker** | proceso que atiende peticiones; más workers, más memoria |
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

**¿Por qué un solo worker?**
Porque el límite de intentos por IP vive en la memoria del proceso: con dos workers cada
uno llevaría su cuenta y el cupo real sería el doble. Y 512 MB de RAM son el recurso
escaso.

**¿Qué es un dyno?**
El contenedor donde corre el programa en Heroku. Uno equivale a un servidor pequeño: 512
MB de RAM y se apaga si no se paga.

**¿Qué es Let's Encrypt y caduca?**
Una autoridad que emite certificados gratis. Caducan a los 90 días; el hosting los renueva
solo, un mes antes.

**¿Por qué Cloudflare en gris y no en naranja?**
En naranja hay dos saltos de proxy: el certificado del hosting fallaría la validación y el
contador de intentos vería la IP de Cloudflare en lugar de la del visitante.

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
R2 es almacenamiento de objetos compatible con S3. El servidor tiene 512 MB y un
despliegue lo reinicia: las fotos durarían poco. En R2 hay 10 GB gratis.

**¿Y si se cae el servidor?**
La web deja de responder. Está asumido: hay un `/healthz` que comprueba que la base
responde, y un aviso diario por GitHub Actions. Con presupuesto de clase no hay réplica.

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
Porque hay un servicio, no veinte. Añadiría capas que hay que mantener y explicar sin
resolver ningún problema de este proyecto.

**¿Cuánto cuesta todo esto?**
12 $/mes (7 de servidor + 5 de base de datos) y 0 € el primer año de dominio. Con el
crédito de estudiante de 312 $ son 26 meses a cero. Stripe y Resend cobran por uso; con
poco volumen, céntimos.

**¿Se puede cambiar de tecnología más adelante?**
Sí, y se ha elegido sabiendo eso. Cambiar de hosting son horas; cambiar de base de datos
es un fin de semana; cambiar de framework es reescribir la web. Por eso las dos primeras
se eligen baratas de cambiar y la tercera se elige una vez.

**¿Qué NO vais a usar?**
React, Docker, Kubernetes, MongoDB, Redis y app móvil. Ninguna resuelve un problema que
tengamos hoy; todas se pueden añadir después.
