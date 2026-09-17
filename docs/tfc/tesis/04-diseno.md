# 4. Diseño

## 4.1 Arquitectura del gateway
Flujo: cliente → `/v1/chat/completions` → resolución de política por tenant → caché → router →
proveedor → cabeceras `X-Nebula-*` → ledger.

## 4.2 Política por tenant
Modo de ruteo, modelos premium permitidos, presupuestos blando y duro, caché (habilitado, umbral
de similitud, antigüedad máxima), fallback, captura de evidencia.

## 4.3 Caché semántico por tenant
Punto en Qdrant = embedding(prompt) + payload {tenant_id, prompt, response, model, created_at}.
Lookup filtra por tenant y por `created_at ≥ ahora − TTL`, con `score_threshold` de la política.
(Implementado en fase 1.)

## 4.4 Router de tres niveles
> PENDIENTE (fase 3): clasificador sobre embedding, salida = probabilidad de aceptabilidad por
> nivel, umbral operable = punto de la frontera.

## 4.5 Frontera costo/calidad
> PENDIENTE (fase 3/4).
