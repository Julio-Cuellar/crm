#!/usr/bin/env python3
"""
E2E del flujo del bot: simulador INBOUND -> backend -> n8n (Gemini) -> callback -> WS.

Ejercita el mismo camino que WhatsApp real pero disparado por /chats/{id}/incoming.
Abre el WebSocket del Inbox (/ws/inbox) ANTES de inyectar el mensaje y verifica que
lleguen DOS eventos new_message:
  1) el INBOUND simulado (eco inmediato del backend)
  2) el OUTBOUND del bot (respuesta asíncrona vía callback de n8n / stub)

Uso:
  ./venv/bin/python scratch/e2e_bot_flow.py \
      --base http://127.0.0.1:8000/api/v1 \
      --email owner@demo.com --password 'Secret123' \
      [--customer-id <uuid>] [--text 'Quiero agendar una cita'] [--timeout 30]

Requiere: paquete `websockets` (ya en venv) + stdlib. Sin dependencias extra.
"""
import argparse
import asyncio
import json
import sys
import urllib.error
import urllib.request

import websockets


def _post(url, body, headers=None):
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, method="POST",
                                 headers={"Content-Type": "application/json", **(headers or {})})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode())


def _get(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode())


def login(base, email, password):
    tok = _post(f"{base}/auth/login", {"email": email, "password": password})
    return tok["accessToken"]


def pick_customer(base, token, customer_id):
    auth = {"Authorization": f"Bearer {token}"}
    if customer_id:
        return customer_id
    customers = _get(f"{base}/customers/", auth)
    if customers:
        cid = customers[0]["id"]
        print(f"[setup] usando cliente existente: {cid} ({customers[0].get('name')})")
        return cid
    created = _post(f"{base}/customers/",
                    {"name": "E2E Bot Tester", "phone": "+521234567890"}, auth)
    print(f"[setup] cliente creado: {created['id']}")
    return created["id"]


async def run(args):
    token = login(args.base, args.email, args.password)
    print("[auth] login OK")
    customer_id = pick_customer(args.base, token, args.customer_id)

    ws_base = args.base.replace("http", "ws", 1)
    ws_url = f"{ws_base}/ws/inbox?token={token}"

    received = []
    async with websockets.connect(ws_url) as ws:
        print(f"[ws] conectado a {ws_url.split('?')[0]}")

        # Inyectar el INBOUND simulado una vez el WS está escuchando.
        auth = {"Authorization": f"Bearer {token}"}
        resp = _post(f"{args.base}/chats/{customer_id}/incoming",
                     {"content": args.text}, auth)
        print(f"[inbound] simulado -> messageId={resp['id']}  content={resp['content']!r}")

        # Recolectar frames hasta timeout o hasta ver el OUTBOUND del bot.
        try:
            while True:
                raw = await asyncio.wait_for(ws.recv(), timeout=args.timeout)
                ev = json.loads(raw)
                received.append(ev)
                print(f"[ws<-] {ev}")
                if ev.get("type") == "handoff":
                    print("[ws] handoff recibido (bot escaló a humano).")
                    break
                # 1 = INBOUND echo, 2 = OUTBOUND bot -> loop completo cerrado.
                new_msgs = [e for e in received if e.get("type") == "new_message"]
                if len(new_msgs) >= 2:
                    break
        except asyncio.TimeoutError:
            print(f"[ws] timeout tras {args.timeout}s sin cerrar el loop.")

    new_msgs = [e for e in received if e.get("type") == "new_message"]
    print("\n===== RESULTADO E2E =====")
    print(f"eventos new_message: {len(new_msgs)}")
    ok = len(new_msgs) >= 2
    if ok:
        print("OK: INBOUND + OUTBOUND(bot) reflejados por WebSocket. Loop cerrado.")
    else:
        print("FALLO: no llegó la respuesta del bot por WS. Revisa:")
        print("  - N8N_BOT_STUB=true (prueba sin n8n)  o  workflow n8n activo + Gemini OK")
        print("  - PUBLIC_BASE_URL apunta al backend accesible desde n8n (IPv4)")
        print("  - N8N_CALLBACK_SECRET coincide entre backend y nodo HTTP de n8n")
    return 0 if ok else 1


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--base", default="http://127.0.0.1:8000/api/v1")
    p.add_argument("--email", required=True)
    p.add_argument("--password", required=True)
    p.add_argument("--customer-id", default=None)
    p.add_argument("--text", default="Hola, quiero agendar una cita para mañana.")
    p.add_argument("--timeout", type=float, default=30.0)
    args = p.parse_args()
    try:
        sys.exit(asyncio.run(run(args)))
    except urllib.error.HTTPError as e:
        print(f"[HTTP {e.code}] {e.read().decode()[:400]}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
