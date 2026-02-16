import asyncio
import re
import os
from aiosmtpd.controller import Controller
from aiohttp import web

# Banco de dados simples em memória
db = {}

class EmailHandler:
    async def handle_DATA(self, server, session, envelope):
        content = envelope.content.decode('utf-8', errors='replace')
        recipient = envelope.rcpt_tos[0].lower()
        print(f"📩 Recebido para: {recipient}", flush=True)
        
        # Busca links de confirmação
        links = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', content)
        for link in links:
            if any(word in link.lower() for word in ["confirm", "verify", "invite", "activate"]):
                db[recipient] = {"status": "confirmed", "link": link}
                print(f"✅ Link capturado para {recipient}: {link}", flush=True)
                
                # Tenta clicar no link via simples requisição HTTP primeiro (muitos sites aceitam)
                try:
                    import requests
                    requests.get(link, timeout=10)
                    print(f"🖱️ Clique HTTP realizado em: {link}", flush=True)
                except:
                    pass
                break
        return '250 OK'

async def check_status(request):
    email = request.match_info['email'].lower()
    return web.json_response(db.get(email, {"status": "pending"}), headers={"Access-Control-Allow-Origin": "*"})

async def list_all(request):
    return web.json_response(db, headers={"Access-Control-Allow-Origin": "*"})

async def main():
    # Porta da API (Easypanel usa 5000 internamente para mapear 8080)
    port = int(os.environ.get("PORT", 5000))
    
    # Inicia SMTP na porta 25
    controller = Controller(EmailHandler(), hostname='0.0.0.0', port=25)
    controller.start()
    print("✅ Servidor SMTP ativo na porta 25", flush=True)
    
    # Inicia API HTTP
    app = web.Application()
    app.router.add_get('/', lambda r: web.Response(text="Servidor Online"))
    app.router.add_get('/check/{email}', check_status)
    app.router.add_get('/list', list_all)
    
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', port).start()
    print(f"🚀 API ativa na porta {port}", flush=True)
    
    await asyncio.Event().wait()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
