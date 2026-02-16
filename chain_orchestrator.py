import asyncio
from typing import List, Dict

class ChainOrchestrator:
    def __init__(self, browser_bot):
        self.browser_bot = browser_bot
        self.email_queue = []
        self.current_index = 0
        self.chain_status = {}
        
    def load_email_list(self, emails: List[str]):
        """Carrega a lista de e-mails para a cadeia"""
        self.email_queue = emails
        for email in emails:
            self.chain_status[email] = {
                "status": "pending",
                "position": emails.index(email),
                "invited_by": emails[emails.index(email) - 1] if emails.index(email) > 0 else None
            }
        print(f"📋 Cadeia carregada com {len(emails)} e-mails", flush=True)
    
    async def process_confirmation(self, confirmed_email: str, invite_link: str, platform_config: Dict):
        """
        Processa a confirmação de um e-mail e avança a cadeia
        
        Args:
            confirmed_email: E-mail que acabou de confirmar
            invite_link: Link de convite que ele recebeu
            platform_config: Configurações da plataforma
        """
        # Atualiza status
        if confirmed_email in self.chain_status:
            self.chain_status[confirmed_email]["status"] = "confirmed"
            
            # Pega o próximo da fila
            current_pos = self.chain_status[confirmed_email]["position"]
            
            if current_pos + 1 < len(self.email_queue):
                next_email = self.email_queue[current_pos + 1]
                
                print(f"🔁 {confirmed_email} confirmou. Avançando para {next_email}...", flush=True)
                
                # Usa o bot para aceitar e convidar o próximo
                result = await self.browser_bot.accept_invite_and_invite_next(
                    invite_link,
                    next_email,
                    platform_config
                )
                
                if result["success"]:
                    self.chain_status[next_email]["status"] = "invited"
                    print(f"✅ Cadeia avançou com sucesso!", flush=True)
                else:
                    print(f"⛔ Cadeia pausada devido a erro", flush=True)
            else:
                print(f"🏁 Fim da cadeia! Todos os e-mails foram processados.", flush=True)
    
    def get_chain_status(self):
        """Retorna o status completo da cadeia"""
        return {
            "total": len(self.email_queue),
            "confirmed": len([e for e in self.chain_status.values() if e["status"] == "confirmed"]),
            "pending": len([e for e in self.chain_status.values() if e["status"] == "pending"]),
            "details": self.chain_status
        }
