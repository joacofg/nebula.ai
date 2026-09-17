# 1. Introducción

## 1.1 Contexto y problema
Las organizaciones que integran LLM pagan por token a proveedores premium aun cuando una fracción
relevante de sus pedidos podría resolverse con modelos locales o con una respuesta ya generada.
Un gateway self-hosted que decide por pedido a qué nivel enviarlo permite recortar ese gasto sin
ceder el control operativo.

## 1.2 Hipótesis
Un gateway con enrutamiento aprendido de tres niveles y caché semántico por tenant reduce el gasto
premium en al menos un 35 % respecto de enviar todo a un proveedor premium, manteniendo una tasa de
respuestas aceptables para un lector no inferior a la del nivel premium económico.

> PENDIENTE (fase 3): fijar el umbral de calidad exacto una vez medida la frontera.

## 1.3 Objetivos
OE1–OE4 según TP4 (ver README).

## 1.4 Alcance y límites
Self-hosted únicamente. Proveedores premium vía OpenRouter. Corpus bilingüe (es/en) de dominio
general. Sin aprendizaje en línea.

## 1.5 Estructura del documento
