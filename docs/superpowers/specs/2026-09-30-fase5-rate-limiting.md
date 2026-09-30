# Spec — Fase 5: rate limiting básico por tenant

Origen: plan maestro `tesis-10x-decisiones-2026-09`; diseño aprobado por Joaquín el 2026-09-30.

## Decisiones

| Tema | Decisión |
|---|---|
| Qué se limita | requests por minuto por tenant |
| Algoritmo | token bucket en memoria (`services/rate_limiter.py`), capacidad = límite, recarga = límite/60 por segundo, lock asyncio, reloj inyectable |
| Configuración | `TenantPolicy.rate_limit_requests_per_minute: int \| None` (1–100 000; `None` = sin límite, default); columna nueva (migración 0003); en `runtime_enforced_fields`; editable en Políticas |
| Alcance | `POST /v1/chat/completions` (con y sin streaming) y `POST /v1/embeddings`, tras autenticar y antes de rutear; admin/health/metrics sin límite |
| Excedido | HTTP 429, `Retry-After` (segundos, entero ≥ 1), `X-Nebula-Route-Target: denied`, `X-Nebula-Route-Reason: rate_limited`; fila en el ledger con `terminal_status="rate_limited"`, `final_route_target="denied"`, `route_reason="rate_limited"`; métrica `nebula_rate_limited_total{tenant}` |
| Headers | `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` (segundos hasta un token) en toda respuesta limitada, incluido streaming |
| Límite cambiado | si la política cambia el límite, el bucket del tenant se reconfigura en la siguiente request (tokens = min(tokens, nueva capacidad)) |
| Multi-proceso | el contador es por proceso; el compose self-hosted corre un solo uvicorn; documentado |

## Fuera de alcance

Redis/distribuido, límites por API key, por tokens o por gasto.

## Criterios de aceptación

1. `make lint`, `make test`, `make console-test` verdes.
2. Con límite 2/min, la tercera request del minuto recibe 429 con `Retry-After`, sin llamar al proveedor ni al embedding; otra tenant no se ve afectada; sin límite nada cambia (sin headers `X-RateLimit-*`).
3. La fila `rate_limited` aparece en el ledger y en la consola.
