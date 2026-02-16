import asyncio
import json
import re
import requests
from aiosmtpd.controller import Controller
from aiohttp import web

# Banco de dados temporário em memória
db = {}

class EmailHandler:
    async def handle_DATA(self, server, session, envelope):
        content = envelope.content.decode('utf-8', errors='replace')
        recipient = envelope.rcpt_tos[0].lower()
        
        print(f"📩 E-mail recebido para: {recipient}", flush=True)
        
        # Busca links no corpo do e-mail
        links = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', content)
        
        for link in links:
            if any(word in link.lower() for word in ["confirm", "verify", "activate", "validate"]):
                try:
                    requests.get(link, timeout=10)
                    db[recipient] = {"status": "confirmed", "link": link}
                    print(f"✅ LINK CLICADO: {link}", flush=True)
                except Exception as e:
                    db[recipient] = {"status": "error", "link": link}
                    print(f"❌ Erro ao clicar: {e}", flush=True)
                break
        
        return '250 OK'

async def check_status(request):
    email = request.match_info['email'].lower()
    data = db.get(email, {"status": "pending"})
    return web.json_response(data, headers={"Access-Control-Allow-Origin": "*"})

async def health(request):
    return web.Response(text="OK")

async def main():
    # Inicia SMTP na porta 25
    controller = Controller(EmailHandler(), hostname='0.0.0.0', port=25)
    controller.start()
    print("✅ Servidor SMTP iniciado na porta 25", flush=True)
    
    # Inicia API
    app = web.Application()
    app.router.add_get('/check/{email}', check_status)
    app.router.add_get('/', health)
    
    runner = web.AppRunner(app)
    await runner.setup()
    # O código ouve na 5000 interna, o Easypanel mapeia para a 8080 externa
    await web.TCPSite(runner, '0.0.0.0', 5000).start()
    
    print("🚀 API iniciada na porta 5000 (Acesse via 8080 no IP)", flush=True)
    await asyncio.Event().wait()

if __name__ == '__main__':
    asyncio.run(main())
