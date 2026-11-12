# contexto del proyecto

## de qué va

cosknot es un marketplace de cosplay. Un sitio donde quien hace ropa, props, pelucas y
accesorios de videojuegos, series, anime y otros mundos de ficción publica sus piezas,
y donde quien las busca las compra o pide un encargo a medida.

Somos el intermediario entre el creador y el comprador. El creador se encarga del
taller y del trabajo; nosotros del escaparate, la ficha de la pieza y el contacto entre
las dos partes. Etsy y Airbnb son la referencia de ese modelo, pero aquí solo hay
cosplay: ropa, props, pelucas y accesorios.

Los creadores que venden en cosknot son usuarios verificados: pasan una revisión del
equipo antes de publicar, y en su ficha aparece la marca de verificado.

El cobro dentro de la web y la comisión por venta quedan para más adelante. En esta
primera versión el trato se cierra por correo con el creador.

## equipo

- Daniel Barrasa: CEO y CMO. Lleva el repositorio, la documentación y la coordinación.
- Jesús Larrazabal: CTO. Lleva el desarrollo, la arquitectura y el despliegue.
- Daniel Torres: CFO. Lleva cuentas, costes e ingresos.

## cómo está ahora

La web está publicada en `https://cosknot.duckdns.org`, con base de datos gestionada,
dominio, HTTPS y despliegue automático desde GitHub.

- El servicio corre en Render, plan free, región de Frankfurt, con gunicorn.
- La base de datos es PostgreSQL 18 en Neon, también en Frankfurt.
- El certificado HTTPS lo pone Render; el dominio es un subdominio gratuito de DuckDNS.
- GitHub Actions pasa las pruebas en cada push, lanza el despliegue y hace una copia
  de la base de datos cada semana.
- Coste actual: 0 € al mes, sin tarjeta.

## stack

Python 3.13, Flask, Jinja, SQLAlchemy, SQLite en local, PostgreSQL en producción,
gunicorn, pytest, Git, GitHub Actions, Render y DuckDNS.

## cómo funciona por dentro

El navegador resuelve `cosknot.duckdns.org` contra el registro A de DuckDNS, que apunta
a la IP de Render. Render termina el HTTPS, arranca la app con gunicorn y usa `/healthz`
para saber si está viva; esa ruta hace un `SELECT 1` contra la base de datos.

En el plan free, Render duerme el servicio a los 15 minutos sin tráfico. La primera
petición después tarda unos 50 segundos por el arranque, y no es un fallo.

## normas que sigo

- Nada de framework de frontend: HTML renderizado en el servidor con Jinja.
- La primera versión se centra en publicar piezas, descubrir creadores y contactar.
  Comprar y cobrar dentro de la web llega después.
- Las pruebas tienen que pasar en local y en GitHub antes de tocar producción.
- Los secretos van en las variables de entorno de Render y en los secretos del
  repositorio, nunca en el código.

Este archivo se mantiene corto. Si cambia la dirección del proyecto, se actualiza.
