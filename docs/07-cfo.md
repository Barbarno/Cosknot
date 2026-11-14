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
| servidor de aplicación (dyno Basic) | 7 $/mes | crédito de estudiante |
| base de datos PostgreSQL (Essential-0) | 5 $/mes | crédito de estudiante |
| dominio `cosknot.me` | 0 € el primer año | cupón del pack |
| DNS y CDN | 0 € | plan gratuito |
| correo transaccional | 0 € hasta 3.000/mes | plan gratuito |
| almacenamiento de fotos | 0 € hasta 10 GB | plan gratuito |
| integración continua | 0 € en repositorio público | plan gratuito |
| **total** | **12 $/mes ≈ 11,10 €** | **0 € de caja durante 24 meses** |

El crédito de estudiante son **312 $** (13 $/mes durante 24 meses): a 12 $/mes cubre
**26 meses**. Después, el coste real es 12 $/mes más unos 12 €/año de dominio.

## punto de equilibrio

```
coste fijo mensual        12,10 €   (11,10 € de servidor + 1,00 € de dominio al año)
comisión por pedido        8 % del importe → 3,60 € con un pedido de 45 €
plan premium               7,99 € al mes

equilibrio solo con pedidos    12,10 ÷ 3,60 = 3,36  →  4 pedidos al mes
equilibrio solo con premium    12,10 ÷ 7,99 = 1,52  →  2 suscriptores
```

**Cuatro pedidos al mes, o dos suscriptores, cubren toda la infraestructura.** Las dos
vías no compiten: el premium cobra a quien quiere que lo vean, la comisión a quien
vende.

### sensibilidad de la comisión

| pedido medio | ingreso por pedido | pedidos/mes para equilibrio |
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
| 20 | 1 | 7,99 € | el dominio y la mitad del servidor |
| 50 | 2–3 | 16–24 € | toda la infraestructura |
| 200 | 10 | 79,90 € | infraestructura y sobra para publicidad |

> Este proyecto no está pensado para ganar dinero, está pensado para demostrar que el
> modelo funciona. Y funciona con muy poco: cuatro encargos al mes de 45 €, o dos
> talleres con plan premium, ya pagan el servidor, el dominio y la base de datos. El
> riesgo no es el margen, es conseguir esos cuatro encargos.
