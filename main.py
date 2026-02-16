async def main():
    # Inicia SMTP na porta 25
    handler = EmailHandler()
    controller = Controller(handler, hostname='0.0.0.0', port=25)
    controller.start()
    print("✅ Servidor SMTP iniciado na porta 25", flush=True)
    
    # Inicia API na porta 5000
    app = web.Application()
    app.router.add_get('/check/{email}', check_status)
    
    # Adiciona um endpoint de teste rápido
    async def health(request):
        return web.Response(text="OK")
    app.router.add_get('/', health)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 5000)
    await site.start()
    
    print("🚀 API iniciada na porta 5000 (Acesse via porta 8080 no IP)", flush=True)
    
    # Mantém o loop rodando
    await asyncio.Event().wait()

if __name__ == '__main__':
    asyncio.run(main())
