from playwright.async_api import async_playwright
import asyncio

class BrowserBot:
    def __init__(self):
        self.browser = None
        self.context = None
        
    async def start(self):
        """Inicia o navegador"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context()
        print("🌐 Navegador iniciado", flush=True)
        
    async def accept_invite_and_invite_next(self, invite_link, next_email, platform_config):
        """
        Aceita um convite e convida o próximo da fila
        
        Args:
            invite_link: Link do convite recebido
            next_email: Próximo e-mail para convidar
            platform_config: Configurações da plataforma (seletores CSS, URLs)
        """
        page = await self.context.new_page()
        
        try:
            # 1. Abre o link do convite
            print(f"🔗 Abrindo link: {invite_link}", flush=True)
            await page.goto(invite_link)
            await page.wait_for_load_state('networkidle')
            
            # 2. Preenche formulário de cadastro
            print(f"📝 Preenchendo formulário...", flush=True)
            
            # Gera dados aleatórios
            import random
            import string
            random_name = ''.join(random.choices(string.ascii_lowercase, k=8))
            random_password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
            
            # Preenche campos (ajuste os seletores para sua plataforma)
            await page.fill(platform_config['name_selector'], random_name)
            await page.fill(platform_config['password_selector'], random_password)
            
            # Clica em criar conta
            await page.click(platform_config['submit_selector'])
            await page.wait_for_load_state('networkidle')
            
            print(f"✅ Conta criada: {random_name}", flush=True)
            
            # 3. Navega até a página de convites
            print(f"👥 Navegando para página de convites...", flush=True)
            await page.goto(platform_config['invite_page_url'])
            await page.wait_for_load_state('networkidle')
            
            # 4. Convida o próximo e-mail
            print(f"📧 Convidando: {next_email}", flush=True)
            await page.fill(platform_config['invite_email_selector'], next_email)
            await page.click(platform_config['invite_submit_selector'])
            
            print(f"🎉 Cadeia avançada! {next_email} foi convidado", flush=True)
            
            return {
                "success": True,
                "account_created": random_name,
                "invited": next_email
            }
            
        except Exception as e:
            print(f"❌ Erro na automação: {e}", flush=True)
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            await page.close()
    
    async def stop(self):
        """Fecha o navegador"""
        if self.browser:
            await self.browser.close()
            print("🛑 Navegador fechado", flush=True)
