# contexto del proyecto cosknot

## propósito

cosknot es una aplicación web y una comunidad para personas que crean y disfrutan del cosplay y del trabajo hecho a mano relacionado con videojuegos series anime y otros mundos de ficción

etsy fue solo una referencia para la idea general de conectar creadores con personas interesadas en su trabajo
cosknot no pretende ser un clon genérico de etsy

## equipo

- ceo y cmo: daniel barrasa
- cto: jesus larrazabal
- cfo: daniel torres

## estado actual

la aplicación está desplegada en producción en `https://cosknot.duckdns.org`, con base de datos gestionada, dominio propio, tls y ci/cd

- el servicio corre en render, plan free, región frankfurt, sobre gunicorn con 2 workers y 4 threads
- la base de datos es postgresql 18 en neon, región aws eu-central-1 (frankfurt), usada con la cadena pooled
- el certificado tls lo emite y renueva render; el dns es un subdominio gratuito de duckdns
- github actions ejecuta las pruebas en cada push y pull request, dispara el despliegue y hace una copia semanal de la base de datos
- coste actual: 0 €/mes, sin tarjeta asociada

## stack

- python 3.13
- flask
- jinja
- sqlalchemy 2.1
- postgresql (neon) en producción
- sqlite en local
- gunicorn
- pytest
- git y github
- github actions
- render
- duckdns

## arquitectura

el navegador resuelve el nombre contra el registro a de duckdns, que apunta a `216.24.57.1`, el ingress de render
render termina el tls, sirve la aplicación con gunicorn y aplica el health check `/healthz`, que ejecuta `SELECT 1`
la aplicación abre la conexión contra postgresql en neon por la cadena pooled, en la misma región
en el plan free render duerme el servicio a los 15 min sin tráfico: la primera petición posterior tarda alrededor de 50 s por el cold start

## convenciones

mantener una aplicación web responsive renderizada en servidor antes de añadir un framework de frontend
la primera versión se centra en el descubrimiento de creadores, las páginas de producto y los listados de vendedores
las pruebas con pytest tienen que pasar en local y en ci antes de tocar producción
los secretos viven en las variables de entorno de render y en los secretos del repositorio, nunca en el código

## regla de actualización

mantener este archivo corto y actualizarlo cuando cambie la dirección del proyecto
