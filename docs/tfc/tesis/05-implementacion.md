# 5. Implementación

## 5.1 Stack
FastAPI + Python 3.12, PostgreSQL 16, Qdrant, Ollama, Next.js 15 (consola).

## 5.2 Componentes del backend
> PENDIENTE (fase 6): tabla de módulos con responsabilidad y líneas.

## 5.3 Consola de operación
> PENDIENTE (fase 4).

## 5.4 Decisiones de ingeniería relevantes
- Fail-open del caché y del embedding (el gateway sigue sirviendo sin Qdrant/Ollama).
- Banner NOT COMPARABLE en benchmarks con dependencias degradadas.
- Migración única derivada de los modelos ORM (fase 1).
