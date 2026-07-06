# Workflows n8n — Bot desacoplado (contrato)

El backend es el único que habla con los canales (WhatsApp, etc.). n8n solo
recibe texto + contexto resumido y responde por un **callback HTTP** al backend.
n8n **no** maneja credenciales de canal ni usa nodos WhatsApp nativos para responder.

## Archivos

- **`JChat_contract.json`** — versión real con **Google Gemini**. El prompt del
  sistema es **individual por tenant/usuario**: llega en `body.agent.prompt` y se
  usa como `systemMessage` del AI Agent. Requiere adjuntar una credencial
  `googlePalmApi` (API key de Gemini) en el nodo *Google Gemini*.
- **`JChat_contract_test.json`** — misma estructura pero con un nodo *IA Stub*
  (sin Gemini). Sirve para probar el cableado end-to-end sin API key. El reply
  incrusta `[prompt:...]` para verificar que el prompt per-tenant llegó.

## Flujo

```
Webhook (/webhook/consultorio-inbound)
  -> Adaptar (lee contrato: message + agent.prompt + context.summary/state)
  -> AI Agent (Gemini)  [systemMessage = agent.prompt  <-- per-usuario]
  -> Parse AI JSON
  -> Construir Reply Contrato (mapea intent/reply -> contrato + memory)
  -> HTTP Callback  (POST body.callbackUrl del backend)
```

## Contrato

**Entrada (backend -> n8n)**: `correlationId, channel, callbackUrl, business,
agent{prompt,config}, conversation, message, context{summary,state,recentTurns,refreshSummary}`.

**Salida (n8n -> backend, POST callbackUrl)**:
```json
{
  "correlationId": "...", "tenantId": "...", "chatId": "...", "customerId": "...",
  "channel": "WHATSAPP",
  "reply": { "type": "TEXT", "content": "...", "mediaUrl": null },
  "memory": { "summary": { "text": "...", "version": 1 } , "statePatch": { "stage": "schedule" } },
  "handoff": false
}
```

- `memory.summary` solo cuando la IA recompacta (o `context.refreshSummary=true`).
- `handoff=true` cuando el intent es `human_escalation` (el backend no auto-responde, escala a humano).

## Uso

1. Importar el workflow en n8n y **activarlo** (solo uno por path a la vez).
2. En `JChat_contract.json`: adjuntar la API key de Gemini al nodo *Google Gemini*.
3. Backend `.env`: `N8N_BOT_STUB=false`,
   `N8N_INBOUND_WEBHOOK_PATH=/webhook/consultorio-inbound`,
   `N8N_BASE_URL=http://<host-n8n>:5678`,
   `PUBLIC_BASE_URL=http://127.0.0.1:8000` (IPv4, evita ECONNREFUSED por `localhost`->`::1`).

## Nota sobre `JChat.json` (raíz del repo)

Es el workflow original completo (Gemini + Google Calendar + Gmail + Postgres +
nodos WhatsApp nativos + recordatorios). `JChat_contract.json` es su adaptación al
contrato desacoplado con prompt per-usuario. Las acciones con efectos externos
(calendario, correo, tickets) se reintegran en el backend (Fase 4), no en n8n.
