import asyncio
import json
import re
import requests
from aiosmtpd.controller import Controller
from aiohttp import web
from browser_automation import BrowserBot
from chain_orchestrator import ChainOrchestrator

# Banco de dados em memória
db = {}

# Configuração da plataforma alvo (AJUSTE PARA SUA PLATAFORMA)
PLATFORM_CONFIG = {
    "name_selector": "input[name='name']",
    "password_selector": "input[name='password']",
    "submit_selector": "button[type='submit']",
    "invite_page_url": "https://suaplataforma.com/invite",
    "invite_email_selector": "input[name='email']",
    "invite_submit_selector": "button.invite-btn"
}

# Inicializa o bot e orquestrador
browser_bot = BrowserBot()
orchestrator = ChainOrchestrator(browser_bot)

class EmailHandler:
    async def handle_DATA(self, server, session, envelope):
        content = envelope.content.decode('utf-8', errors='replace')
        recipient = envelope.rcpt_tos[0].lower()
        
        print(f"📩 E-mail recebido para: {recipient}", flush=True)
        
        links = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', content)
        
        for link in links:
            if any(word in link.lower() for word in ["confirm", "verify", "activate", "validate", "invitation"]):
                try:
                    # Salva no banco
                    db[recipient] = {
                        "status": "confirmed",
                        "link": link
                    }
                    
                    print(f"✅ Link capturado: {link}", flush=True)
                    
                    # AQUI É A MÁGICA: Processa a cadeia
                    await orchestrator.process_confirmation(recipient, link, PLATFORM_CONFIG)
                    
                except Exception as e:
                    print(f"❌ Erro: {e}", flush=True)
                break
        
        return '250 OK'

# APIs
async def check_status(request):
    email = request.match_info['email'].lower()
    data = db.get(email, {"status": "pending"})
    return web.json_response(data, headers={"Access-Control-Allow-Origin": "*"})

async def get_chain_status(request):
    """Novo endpoint para ver o status da cadeia"""
    status = orchestrator.get_chain_status()
    return web.json_response(status, headers={"Access-Control-Allow-Origin": "*"})

async def load_chain(request):
    """Endpoint para carregar a lista de e-mails"""
    data = await request.json()
    emails = data.get("emails", [])
    orchestrator.load_email_list(emails)
    return web.json_response({"success": True, "loaded": len(emails)}, headers={"Access-Control-Allow-Origin": "*"})

async def main():
    # Inicia o navegador
    await browser_bot.start()
    
    # Inicia SMTP
    controller = Controller(EmailHandler(), hostname='0.0.0.0', port=25)
    controller.start()
    print("✅ Servidor SMTP iniciado na porta 25", flush=True)
    
    # Inicia API
    app = web.Application()
    app.router.add_get('/', lambda r: web.Response(text="OK"))
    app.router.add_get('/check/{email}', check_status)
    app.router.add_get('/chain/status', get_chain_status)
    app.router.add_post('/chain/load', load_chain)
    
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', 5000).start()
    
    print("🚀 Sistema de Cadeia iniciado!", flush=True)
    print("📡 Novos endpoints:", flush=True)
    print("   - POST /chain/load (carrega lista de e-mails)", flush=True)
    print("   - GET /chain/status (status da cadeia)", flush=True)
    
    await asyncio.Event().wait()

if __name__ == '__main__':
    asyncio.run(main())
