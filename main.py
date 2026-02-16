import asyncio
from aiosmtpd.controller import Controller
import re
import requests
from datetime import datetime
import json
import os

HOST = os.getenv("SMTP_HOST", "0.0.0.0")
PORT = int(os.getenv("SMTP_PORT", "25"))
MAX_LINKS = int(os.getenv("MAX_LINKS", "3"))
TIMEOUT_SECONDS = int(os.getenv("HTTP_TIMEOUT", "15"))

LOG_FILE = os.getenv("LOG_FILE", "email_clicks.log")
CONFIRMATIONS_FILE = os.getenv("CONFIRMATIONS_FILE", "confirmations.json")

class ClickBotHandler:
    def log(self, message: str):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] {message}"
        print(line, flush=True)
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass

    def save_confirmation(self, data: dict):
        confirmations = []
        if os.path.exists(CONFIRMATIONS_FILE):
            try:
                with open(CONFIRMATIONS_FILE, "r", encoding="utf-8") as f:
                    confirmations = json.load(f)
            except Exception:
                confirmations = []

        confirmations.append(data)
        try:
            with open(CONFIRMATIONS_FILE, "w", encoding="utf-8") as f:
                json.dump(confirmations, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    async def handle_DATA(self, server, session, envelope):
        recipient = envelope.rcpt_tos[0] if envelope.rcpt_tos else "desconhecido"
        sender = envelope.mail_from or "desconhecido"

        self.log("📩 E-mail recebido")
        self.log(f"   De: {sender}")
        self.log(f"   Para: {recipient}")

        try:
            content = envelope.content.decode("utf-8", errors="replace")
        except Exception:
            content = str(envelope.content)

        patterns = [
            r'https?://[^\s<>"]+(?:confirm|verify|accept|join|token|activate|invitation)[^\s<>"]*',
            r'https?://[^\s<>"]+[?&]token=[^\s<>"]+',
            r'https?://[^\s<>"]+[?&]code=[^\s<>"]+',
        ]

        links = []
        for p in patterns:
            links.extend(re.findall(p, content, flags=re.IGNORECASE))
        links = list(dict.fromkeys(links))  # dedupe mantendo ordem

        if not links:
            self.log("   ❓ Nenhum link de confirmação encontrado")
            self.log("   " + "=" * 60)
            return "250 Message accepted for delivery"

        self.log(f"   🔗 {len(links)} link(s) encontrado(s)")

        headers = {
            "User-Agent": os.getenv(
                "USER_AGENT",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        }

        for link in links[:MAX_LINKS]:
            self.log(f"   Clicando em: {link[:120]}")

            try:
                resp = requests.get(
                    link,
                    headers=headers,
                    timeout=TIMEOUT_SECONDS,
                    allow_redirects=True,
                )
                self.log(f"   ↪ Status: {resp.status_code}")

                self.save_confirmation(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "email": recipient,
                        "sender": sender,
                        "link": link,
                        "status": resp.status_code,
                    }
                )

            except requests.exceptions.Timeout:
                self.log("   ⏱️ Timeout ao acessar o link")
                self.save_confirmation(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "email": recipient,
                        "sender": sender,
                        "link": link,
                        "status": "timeout",
                    }
                )
            except Exception as e:
                self.log(f"   ❌ Erro ao acessar link: {str(e)[:200]}")
                self.save_confirmation(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "email": recipient,
                        "sender": sender,
                        "link": link,
                        "status": "error",
                        "error": str(e)[:200],
                    }
                )

            await asyncio.sleep(1)

        self.log("   " + "=" * 60)
        return "250 Message accepted for delivery"


def main():
    print("=" * 60)
    print("🤖 SMTP Auto-Click Bot")
    print("=" * 60)
    print(f"Host: {HOST}")
    print(f"Port: {PORT}")
    print(f"Log file: {LOG_FILE}")
    print(f"Confirmations file: {CONFIRMATIONS_FILE}")
    print("=" * 60, flush=True)

    controller = Controller(ClickBotHandler(), hostname=HOST, port=PORT)
    controller.start()

    try:
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        controller.stop()


if __name__ == "__main__":
    main()
