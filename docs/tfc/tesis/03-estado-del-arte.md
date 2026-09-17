# 3. Estado del arte

| Sistema | Tipo | Enrutamiento | Caché | Cifra publicada | Fuente |
|---|---|---|---|---|---|
| RouteLLM (LMSYS, 2024) | router aprendido | MF / BERT / causal LLM | no | hasta 85 % menos costo con 95 % de la calidad de GPT-4 en MT-Bench | Ong et al. 2024 |
| FrugalGPT (Stanford, 2023) | cascada | scorer por respuesta | sí (prompt) | hasta 98 % menos costo igualando GPT-4 | Chen et al. 2023 |
| GPTCache | caché semántico | no | sí | — | repo zilliztech |
| LiteLLM | proxy | reglas/fallback | sí (exacto y semántico) | — | docs |
| Portkey | gateway comercial | reglas condicionales | sí | — | docs |
| OpenRouter Auto Router | router hospedado | propietario (NotDiamond) | no | — | docs |

> PENDIENTE (fase 6): verificar cada cifra contra la fuente primaria y completar columnas.
> Decisión de diseño de la tesis: no se corren benchmarks de terceros; se comparan cifras publicadas.

## 3.1 Qué no cubre ninguno de los anteriores
Aislamiento por tenant del caché con política operable, frontera costo/calidad visible y ajustable
por el operador, y validación de los jueces contra un lector humano.
