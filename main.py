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
        
        # Busca links no corpo do e-mail
        links = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', content)
        
        found_link = None
        for link in links:
            # Filtra links que parecem ser de confirmação
            if any(word in link.lower() for word in ["confirm", "verify", "activate", "validate"]):
                found_link = link
                try:
                    # O ROBÔ CLICA NO LINK AQUI
                    requests.get(link, timeout=10)
                    db[recipient] = {"status": "confirmed", "link": link}
                    print(f"✅ CONFIRMADO: {recipient}")
                except:
                    db[recipient] = {"status": "error", "link": link}
                break
        
        return '250 OK'

# API para o Lovable consultar
async def check_status(request):
    email = request.match_info['email'].lower()
    data = db.get(email, {"status": "pending"})
    return web.json_response(data, headers={
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type"
    })

async def main():
    # Inicia SMTP na porta 25
    controller = Controller(EmailHandler(), hostname='0.0.0.0', port=25)
    controller.start()
    
    # Inicia API na porta 5000
    app = web.Application()
    app.router.add_get('/check/{email}', check_status)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', 5000).start()
    
    print("🚀 Servidor Duplo Rodando: SMTP(25) e API(5000)")
    await asyncio.Event().wait()

if __name__ == '__main__':
    asyncio.run(main())
