// Illustrative ledger rows (shape of the real ledger with the learned router on).
// Prompts come from docs/demo-runbook.md; costs follow OpenRouter list prices.
window.LEDGER = [
  { t: "14:32:07", id: "7f3a09c2", prompt: "¿Cuál es la capital de Australia?", tier: "local", model: "qwen2.5:7b", tok: 38, cost: 0, lat: 2.1, status: "completado" },
  { t: "14:31:52", id: "b91e4d17", prompt: "¿Por qué los boletos de avión están tan caros ahora?", tier: "economy", model: "claude-haiku-4.5", tok: 412, cost: 0.0018, lat: 3.6, status: "completado", pl: 0.41, pe: 0.95 },
  { t: "14:31:20", id: "04dd8a5e", prompt: "Escribe una función en Python con la criba de Eratóstenes, con tests.", tier: "frontier", model: "gpt-4.1", tok: 690, cost: 0.005, lat: 4.9, status: "completado" },
  { t: "14:30:58", id: "c5e27b90", prompt: "Resume en una frase qué es la caché semántica.", tier: "cache", model: "—", tok: 22, cost: 0, lat: 0.04, status: "caché" },
  { t: "14:30:41", id: "e1b6f033", prompt: "Traduce al inglés: el envío llega el martes.", tier: "local", model: "qwen2.5:7b", tok: 31, cost: 0, lat: 1.8, status: "completado" },
  { t: "14:30:12", id: "9a0c52de", prompt: "Explica la diferencia entre TCP y UDP.", tier: "economy", model: "claude-haiku-4.5", tok: 356, cost: 0.0016, lat: 3.1, status: "completado" },
  { t: "14:29:47", id: "3d7e81af", prompt: "Redacta un correo breve para mover la reunión al jueves.", tier: "local", model: "qwen2.5:7b", tok: 118, cost: 0, lat: 4.4, status: "completado" },
  { t: "14:29:30", id: "58fb6c21", prompt: "Analiza si a un laboratorio le conviene comprar GPUs o alquilar nube.", tier: "frontier", model: "gpt-4.1", tok: 812, cost: 0.0061, lat: 6.2, status: "completado" },
  { t: "14:29:02", id: "a2c49e7d", prompt: "¿Qué es un webhook?", tier: "denied", model: "—", tok: 0, cost: 0, lat: 0, status: "límite (429)" },
];
window.renderLedger = function (tbody, fmt) {
  tbody.innerHTML = window.LEDGER.map((r, i) => fmt(r, i)).join("");
};
