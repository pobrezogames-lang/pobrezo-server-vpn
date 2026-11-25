
import os
import json
import hmac
import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI(title="POBREZO VPN SERVER")

SECRET = os.environ.get("VPN_SECRET", "")


@app.get("/")
async def home():
    return {
        "name": "POBREZO VPN",
        "status": "online",
        "version": "2.0"
    }


@app.websocket("/ws")
async def tunnel(ws: WebSocket):
    await ws.accept()

    try:
        auth = json.loads(await ws.receive_text())
        supplied = str(auth.get("token", ""))

        if not SECRET or not hmac.compare_digest(
            supplied, SECRET
        ):
            await ws.send_json({
                "status": "error",
                "message": "Autenticacao recusada"
            })
            await ws.close(code=1008)
            return

        ip = "indisponivel"

        try:
            async with httpx.AsyncClient(
                timeout=8
            ) as client:
                result = await client.get(
                    "https://api.ipify.org?format=json"
                )
                ip = result.json().get("ip", ip)
        except Exception:
            pass

        await ws.send_json({
            "status": "connected",
            "server": "POBREZO VPN",
            "version": "2.0",
            "server_ip": ip,
            "protocol": "WSS/TLS"
        })

        while True:
            message = json.loads(
                await ws.receive_text()
            )

            if message.get("action") == "ping":
                await ws.send_json({
                    "action": "pong"
                })

    except WebSocketDisconnect:
        pass
    except Exception as error:
        print("Connection error:", error)
        try:
            await ws.close()
        except Exception:
            pass
