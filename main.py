import asyncio
import os
from aiosmtpd.controller import Controller
from aiohttp import web

# Banco de dados em memória
db = {}

class EmailHandler:
    async def handle_DATA(self, server, session, envelope):
        print(f"📩 E-mail recebido!", flush=True)
        return '250 OK'

async def main():
    # 1. Configuração de Portas
    # Usamos 1025 para o SMTP (evita erro de permissão)
    # Usamos 5000 para a API (padrão do Easypanel)
    smtp_port = 1025
    api_port = int(os.environ.get("PORT", 5000))

    print(f"Starting services...", flush=True)

    # 2. Inicia SMTP
    try:
        handler = EmailHandler()
        controller = Controller(handler, hostname='0.0.0.0', port=smtp_port)
        controller.start()
        print(f"✅ SMTP rodando na porta {smtp_port}", flush=True)
    except Exception as e:
        print(f"❌ Erro ao iniciar SMTP: {e}", flush=True)

    # 3. Inicia API HTTP
    app = web.Application()
    app.router.add_get('/', lambda r: web.Response(text="Servidor Online"))
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', api_port)
    await site.start()
    print(f"🚀 API rodando na porta {api_port}", flush=True)

    # Mantém o loop vivo
    while True:
        await asyncio.sleep(3600)

if __name__ == '__main__':
    asyncio.run(main())
