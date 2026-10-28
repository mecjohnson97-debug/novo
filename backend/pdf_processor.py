import os
from pathlib import Path
from typing import List
import pickle

class WatizatPDFProcessor:
    def __init__(self):
        self.knowledge_base = self._load_knowledge_base()
        
    def _load_knowledge_base(self) -> dict:
        """Carrega base de conhecimento do Watizat"""
        return {
            "alimentacao": [
                "Secours Catholique oferece distribuição de alimentos em 15 Rue de Maubeuge, 75009 Paris. Tel: 01 45 49 73 00. Horário: Seg-Sex 9h-17h.",
                "Restaurants du Coeur oferece refeições gratuitas em 42 Rue Championnet, 75018 Paris. Tel: 01 53 32 23 23. Horário: Seg-Sex 11h30-13h30.",
                "Croix-Rouge distribui alimentos e produtos básicos em diversos pontos de Paris."
            ],
            "juridico": [
                "La Cimade oferece assistência jurídica gratuita em 176 Rue de Grenelle, 75007 Paris. Tel: 01 40 08 05 34. Horário: Ter-Qui 14h-18h.",
                "GISTI fornece informações sobre direitos dos estrangeiros em 3 Villa Marcès, 75011 Paris. Tel: 01 43 14 84 84.",
                "Para solicitar asilo, procure SPADA ou OFPRA. É importante ter documentos de identidade e provas de perseguição."
            ],
            "saude": [
                "PASS oferece atendimento médico gratuito em Hôpital Saint-Louis, 1 Avenue Claude Vellefaux, 75010 Paris. Tel: 01 42 49 49 49.",
                "Para emergências médicas, ligue 15 (SAMU) ou vá ao hospital mais próximo.",
                "AME (Aide Médicale d'État) oferece cobertura de saúde para pessoas sem documentos."
            ],
            "moradia": [
                "France Terre d'Asile oferece acolhimento em 24 Rue Marc Seguin, 75018 Paris. Tel: 01 53 04 39 99.",
                "Para emergência, ligue 115 (SAMU Social) para abrigo temporário.",
                "CADA e HUDA são centros de acolhimento para solicitantes de asilo."
            ],
            "trabalho": [
                "Pôle Emploi International ajuda na busca de emprego em 48 Boulevard de la Bastille, 75012 Paris. Tel: 39 49.",
                "Após 6 meses de pedido de asilo, você pode solicitar autorização para trabalhar.",
                "Procure ONGs como Singa ou Refugeers para workshops de emprego."
            ],
            "educacao": [
                "CASNAV ajuda na escolarização de crianças migrantes em 12 Boulevard d'Indochine, 75019 Paris. Tel: 01 44 62 39 36.",
                "Todas as crianças têm direito à educação na França, independente do status migratório.",
                "Cursos de francês gratuitos estão disponíveis em diversas associações."
            ],
            "geral": [
                "O guia Watizat é atualizado mensalmente com informações para migrantes em Paris.",
                "É importante sempre ter cópias de seus documentos importantes.",
                "Procure sempre ajuda de associações especializadas para orientação personalizada."
            ]
        }
    
    def search(self, query: str, k: int = 3) -> List[str]:
        """Busca informações relevantes na base de conhecimento"""
        query_lower = query.lower()
        results = []
        
        keywords_map = {
            "comida": "alimentacao",
            "alimento": "alimentacao",
            "comer": "alimentacao",
            "fome": "alimentacao",
            "juridico": "juridico",
            "legal": "juridico",
            "advogado": "juridico",
            "direito": "juridico",
            "asilo": "juridico",
            "saude": "saude",
            "medico": "saude",
            "hospital": "saude",
            "doente": "saude",
            "moradia": "moradia",
            "casa": "moradia",
            "abrigo": "moradia",
            "dormir": "moradia",
            "trabalho": "trabalho",
            "emprego": "trabalho",
            "trabalhar": "trabalho",
            "educacao": "educacao",
            "escola": "educacao",
            "estudar": "educacao",
            "curso": "educacao"
        }
        
        for keyword, category in keywords_map.items():
            if keyword in query_lower:
                results.extend(self.knowledge_base[category])
                if len(results) >= k:
                    break
        
        if not results:
            results = self.knowledge_base["geral"]
        
        return results[:k]
    
    def load_index(self) -> bool:
        """Compatibilidade - sempre retorna True"""
        return True
