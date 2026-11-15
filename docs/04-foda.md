# matriz FODA

```
                 INTERNO                              EXTERNO
        ┌────────────────────────────────┬────────────────────────────────┐
  +     │ FORTALEZAS                     │ OPORTUNIDADES                  │
        │ · nicho concreto: solo cosplay │ · comunidades hispanas activas │
        │ · comisión 8 % frente al 10 %  │ · salones y eventos como canal │
        │   real de Etsy                 │ · creadores que ya venden por  │
        │ · pedido con estados y         │   mensajes directos y no       │
        │   mensajería, no un chat       │   tienen escaparate            │
        │ · coste de infraestructura 0 € │ · hueco en español: Etsy está  │
        │ · equipo que conoce el hobby   │   en inglés y en dólares       │
        │ · identidad visual propia      │ · temporadas: cada salón mueve │
        │                                │   encargos con meses de margen │
        ├────────────────────────────────┼────────────────────────────────┤
  -     │ DEBILIDADES                    │ AMENAZAS                       │
        │ · marca desconocida, 0 usuarios│ · Etsy y AliExpress por precio │
        │ · catálogo de ejemplo, no real │ · Instagram como canal de compra│
        │ · sin valoraciones todavía     │ · la comisión del cobro se come│
        │ · dependemos de Google y Neon: │   margen en pedidos pequeños   │
        │   si caen, la web no responde  │ · propiedad intelectual de los │
        │ · el creador debe conectar     │   personajes (zona gris legal) │
        │   una cuenta de cobro          │ · depender de que Google y     │
        │ · sin app móvil                │   Neon mantengan lo gratuito   │
        └────────────────────────────────┴────────────────────────────────┘
```

## las dos que hay que defender con datos

**Debilidad: cero usuarios.** Se responde con el plan, no con optimismo. El lanzamiento
es por comunidades concretas (servidores de Discord de cosplay en español, salones) y no
abierto al público; las primeras 20 fichas de taller se captan a mano hablando con
creadores, uno por uno.

**Amenaza: la comisión del cobro.** En un pedido de 10 €, Stripe se lleva 0,40 €
(1,5 % + 0,25 €) y nuestra comisión son 0,80 €. Por debajo de ~5 € el modelo no tiene
sentido, y por eso el precio mínimo de una pieza no es una decisión estética: es una
decisión de margen.

## qué hacemos con cada cuadrante

| cuadrante | acción |
|---|---|
| fortalezas | usarlas en el discurso: nicho, comisión y pedido ordenado |
| oportunidades | entrar por comunidad y salón, no por publicidad |
| debilidades | lanzamiento cerrado y fichas captadas a mano |
| amenazas | precio mínimo de pieza y hosting reversible: Heroku con crédito como plan B |
