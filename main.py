import asyncio
import json
import re
import requests
from aiosmtpd.controller import Controller
from aiohttp import web

# Banco de dados em memória para armazenar status dos e-mails
db = {}

class EmailHandler:
    """Classe que processa e-mails recebidos na porta 25"""
    async def handle_DATA(self, server, session, envelope):
        content = envelope.content.decode('utf-8', errors='replace')
        recipient = envelope.rcpt_tos[0].lower()
        
        print(f"📩 E-mail recebido para: {recipient}", flush=True)
        
        # Busca todos os links no corpo do e-mail
        links = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', content)
        
        # Procura por links de confirmação
        for link in links:
            if any(word in link.lower() for word in ["confirm", "verify", "activate", "validate", "verification"]):
                try:
                    # Clica no link automaticamente
                    response = requests.get(link, timeout=10)
                    db[recipient] = {
                        "status": "confirmed",
                        "link": link,
                        "http_code": response.status_code
                    }
                    print(f"✅ LINK CLICADO: {link} | Status: {response.status_code}", flush=True)
                except Exception as e:
                    db[recipient] = {
                        "status": "error",
                        "link": link,
                        "error": str(e)
                    }
                    print(f"❌ Erro ao clicar no link: {e}", flush=True)
                break
        
        return '250 OK'

# API para o Lovable consultar o status dos e-mails
async def check_status(request):
    """Endpoint: /check/{email} - Retorna o status de um e-mail específico"""
    email = request.match_info['email'].lower()
    data = db.get(email, {"status": "pending"})
    
    return web.json_response(data, headers={
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type"
    })

async def health(request):
    """Endpoint: / - Verifica se a API está online"""
    return web.Response(text="OK", headers={
        "Access-Control-Allow-Origin": "*"
    })

async def list_all(request):
    """Endpoint: /list - Lista todos os e-mails monitorados"""
    return web.json_response({
        "total": len(db),
        "emails": db
    }, headers={
        "Access-Control-Allow-Origin": "*"
    })

async def main():
    """Função principal que inicia o servidor SMTP e a API"""
    
    # Inicia o servidor SMTP na porta 25
    controller = Controller(EmailHandler(), hostname='0.0.0.0', port=25)
    controller.start()
    print("✅ Servidor SMTP iniciado na porta 25", flush=True)
    
    # Configura as rotas da API
    app = web.Application()
    app.router.add_get('/', health)
    app.router.add_get('/check/{email}', check_status)
    app.router.add_get('/list', list_all)
    
    # Inicia a API na porta 5000
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 5000)
    await site.start()
    
    print("🚀 API iniciada na porta 5000 (Acesse via porta 8080 no IP externo)", flush=True)
    print("📡 Endpoints disponíveis:", flush=True)
    print("   - http://148.230.76.228:8080/ (health check)", flush=True)
    print("   - http://148.230.76.228:8080/check/{email} (consultar status)", flush=True)
    print("   - http://148.230.76.228:8080/list (listar todos)", flush=True)
    
    # Mantém o servidor rodando indefinidamente
    await asyncio.Event().wait()

if __name__ == '__main__':
    asyncio.run(main())
