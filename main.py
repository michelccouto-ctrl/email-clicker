from aiohttp import web
import asyncio
import os

async def hello(request):
    return web.Response(text="Servidor OK")

async def main():
    port = int(os.environ.get("PORT", 5000))
    app = web.Application()
    app.router.add_get("/", hello)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    print(f"✅ API rodando na porta {port}", flush=True)

    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
