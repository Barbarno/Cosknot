# CFO: ingresos, costes y punto de equilibrio

## ingresos

Tres vías. La primera es la del día a día; las otras dos son las que sostienen un mes
sin ventas.

| vía | precio | cuándo se cobra |
|---|---|---|
| **comisión por venta** | **8 %** del pedido | en el pago; el 92 % va al creador |
| **plan premium del taller** | **7,99 €/mes** o **79,90 €/año** | por adelantado, sin renovación automática |
| **destacar una pieza** | **2,99 €** por 7 días | cuando el taller quiere empujar una pieza suelta |

El plan premium sube el tope de piezas publicadas de 10 a 50, pone al taller delante en
los listados y añade etiqueta. **No rebaja la comisión**: si lo hiciera, el ingreso se
comería a sí mismo.

**Por qué comisión primero.** Un creador que empieza no paga 8 €/mes por algo que
todavía no le trae ventas; la comisión solo se cobra cuando hay dinero, y eso es lo que
hace que se registre. El premium llega después, cuando tiene catálogo y le falta que lo
vean.

**Por qué no anuncios.** Con el tráfico de un proyecto pequeño, la publicidad daría
céntimos y ensuciaría una web cuyo valor es la confianza en el escaparate.

### de dónde salen esos precios

| servicio | plan de vendedor | destacar |
|---|---|---|
| Ko-fi Gold | 6 $/mes | — |
| Folksy Plus | 7,50 £/mes | — |
| **cosknot** | **7,99 €/mes** | **2,99 € / 7 días** |
| Big Cartel Gold | 9,99 $/mes | — |
| Etsy Plus | 10 $/mes | 0,20 $ por anuncio |
| eBay Store Basic | 21,95 $/mes | 1–20 % por venta promocionada |
| Vinted | gratis para el vendedor | 0,70–2,00 € por subir |
| Wallapop | gratis para el vendedor | 1,99–6,99 € por destacar |

La banda del mercado para visibilidad de vendedor en un marketplace pequeño es
**6–12 $/mes**; 7,99 € cae en el medio. Para destacados, el grueso del mercado está en
**2–4 €**. Fuentes: páginas de precios públicas de cada servicio, consultadas el
14 de noviembre de 2026.

## costes

### inversión inicial: 0 €

Todo el software es libre, el dominio del primer año sale del pack de estudiante y la
infraestructura arranca en capas gratuitas. El trabajo es del equipo.

### mantenimiento mensual

| concepto | coste | quién lo cubre |
|---|---|---|
| servidor de aplicación (Google Cloud Run) | 0 € dentro del tramo gratuito | plan gratuito |
| base de datos PostgreSQL (Neon) | 0 € hasta 0,5 GB | plan gratuito |
| dominio `cosknot.me` | 0 € el primer año | cupón del pack |
| DNS y CDN | 0 € | plan gratuito |
| correo transaccional | 0 € hasta 3.000/mes | plan gratuito |
| almacenamiento de fotos | 0 € hasta 10 GB | plan gratuito |
| integración continua | 0 € en repositorio público | plan gratuito |
| **total** | **0 €/mes** | **0 € de caja** |

El tramo gratuito de Cloud Run son **2 millones de peticiones, 180.000 vCPU-segundo y
360.000 GiB-segundo al mes**; Neon da **0,5 GB** de base con copias. Con 100 talleres el
catálogo no llega a 50 MB y el tráfico a unas 20.000 peticiones al mes: hay un margen de
**cien veces** antes de que aparezca la primera factura. Y solo se cobra lo que se usa, así
que una web sin visitas cuesta exactamente cero.

A partir del segundo año, el dominio son unos **12 €/año ≈ 1,00 €/mes**. Ese es hoy el
coste fijo completo del proyecto.

Los 90 días y los 300 $ que ofrece Google al abrir la cuenta son **la prueba gratuita**,
no el tramo gratuito: lo que caduca es el crédito, no las capas gratuitas. Al terminar la
prueba hay que pulsar «pasar a cuenta de pago» para que los servicios no se paren, y eso
no genera ningún cargo mientras el consumo siga por debajo de esos límites. Lo que sí
exige tarjeta es abrir la facturación, igual que la exigía Heroku.

### el crédito de estudiante: intacto, y como red

Los **312 $** del pack de estudiante (13 $/mes durante 24 meses) siguen **sin gastarse** y no
están aplicados a ningún proveedor: no hay ninguna cuenta creada, así que no corre ningún
reloj. El pack no se canjea hasta el día antes de la demostración en vivo.

Sirve para lo que sirve un seguro: **si mañana Cloud Run cambia de condiciones**, el mismo
código se despliega en Heroku con un `git push` y los 312 $ cubren **26 meses a 12 $/mes**
(7 de servidor + 5 de base de datos). Esa es la alternativa evaluada y disponible, no un
plan que haya que montar a mano.

### cuándo deja de ser gratis

| si algún día… | cuándo pasa | qué costaría |
|---|---|---|
| se supera el tramo de Cloud Run | > 2 M peticiones/mes: unas 100 veces este proyecto | unos céntimos por cada millón extra |
| la base pasa de 0,5 GB | > 10.000 piezas con sus mensajes | Neon Launch: 19 $/mes |
| se quiere quitar el arranque en frío | el primer día si molesta | 1 instancia mínima: ~5 $/mes |
| se quiere pagar todo en un solo proveedor | cuando sobre tiempo, no antes | Heroku: 12 $/mes, con el crédito |

Ninguna de las cuatro es una factura hoy, y las cuatro están dichas antes de que nadie
pregunte. Eso es lo que se pide a un plan de costes: no que sea cero, sino que se sepa
dónde está el primer euro.

## punto de equilibrio

```
coste fijo mensual hoy     1,00 €    (12 €/año de dominio, repartidos mes a mes)
coste si algún día se paga 12,10 €   (11,10 € de infraestructura + 1,00 € de dominio)
comisión por pedido        8 % del importe → 3,60 € con un pedido de 45 €
plan premium               7,99 € al mes

equilibrio hoy                 1,00 ÷ 3,60 = 0,28  →  1 pedido al mes
equilibrio pagando todo       12,10 ÷ 3,60 = 3,36  →  4 pedidos al mes
equilibrio pagando todo        12,10 ÷ 7,99 = 1,52  →  2 suscriptores
```

**Un solo pedido al mes cubre el proyecto entero**, porque la infraestructura no cuesta
nada: lo único que se paga hoy es el dominio del segundo año. Y con la fila de abajo queda
dicho lo otro, que es lo que de verdad importa: **incluso pagando la infraestructura
entera, cuatro pedidos al mes o dos suscriptores la cubren**. El plan no se sostiene por
ser gratis; se sostiene porque el margen es enorme frente al coste.

Las dos vías no compiten: el premium cobra a quien quiere que lo vean, la comisión a quien
vende.

### sensibilidad de la comisión

La tabla dice cuántos pedidos al mes harían falta **si algún día hubiera que pagar los
12,10 €** de infraestructura y dominio. Es el escenario pesimista, y es el que se enseña.

| pedido medio | ingreso por pedido | pedidos/mes para cubrir 12,10 € |
|---|---|---|
| 15 € | 1,20 € | 11 |
| 25 € | 2,00 € | 7 |
| 45 € | 3,60 € | 4 |
| 80 € | 6,40 € | 2 |

### coste real de un pedido

| concepto | en un pedido de 45 € |
|---|---|
| cobro de Stripe (1,5 % + 0,25 €) | 0,93 € |
| comisión de cosknot (8 %) | 3,60 € |
| **queda para el creador** | **40,47 €** |

En pedidos por debajo de ~5 € el modelo no tiene sentido: el cobro fijo se come la
comisión. Por eso hay un precio mínimo de pieza.

## escenario honesto para la exposición

| talleres | premium (5 %) | ingreso/mes | cubre |
|---|---|---|---|
| 20 | 1 | 7,99 € | el dominio del año, ocho veces |
| 50 | 2–3 | 16–24 € | el dominio y, si hiciera falta, la infraestructura entera |
| 200 | 10 | 79,90 € | todo, y sobra para publicidad |

> Este proyecto no está pensado para ganar dinero, está pensado para demostrar que el
> modelo funciona. Y funciona con muy poco: hoy la infraestructura cuesta 0 €, así que
> **un solo encargo al mes de 45 € ya cubre lo único que se paga, el dominio**. Y en el
> escenario pesimista —pagar servidor, base de datos y dominio— bastan cuatro encargos al
> mes o dos talleres con plan premium. El riesgo no es el margen, es conseguir esos cuatro
> encargos.
