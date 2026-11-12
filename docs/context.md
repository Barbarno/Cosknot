# contexto del proyecto

## de qué va

cosknot es una web para gente a la que le gusta el cosplay y el trabajo hecho a mano
relacionado con videojuegos, series, anime y otros mundos de ficción. La idea es juntar
en un sitio a quien hace la ropa, los props y los accesorios, y a quien los busca.

Etsy me sirvió de referencia para entender la idea de conectar creadores con gente
interesada, pero cosknot no quiere ser un clon. En esta primera versión solo hay
descubrimiento y contacto.

## equipo

- Daniel Barrasa: idea, documentación y GitHub.
- Jesús Larrazabal: desarrollo y despliegue.
- Daniel Torres: cuentas y costes.

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
- La primera versión se centra en descubrir creadores y contactar, nada más.
- Las pruebas tienen que pasar en local y en GitHub antes de tocar producción.
- Los secretos van en las variables de entorno de Render y en los secretos del
  repositorio, nunca en el código.

Este archivo se mantiene corto. Si cambia la dirección del proyecto, se actualiza.
