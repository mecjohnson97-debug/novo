"""
Sistema de Respostas Automáticas baseado em Refugies.info
Fornece informações úteis automaticamente quando alguém posta pedindo ajuda
"""

AUTO_RESPONSES = {
    "work": {
        "title": "🔍 Recursos para Emprego",
        "content": """Olá! Vi que você está procurando ajuda com trabalho. Aqui estão alguns recursos que podem ajudar:

📌 **France Travail (Pôle emploi)**
• Serviço público para encontrar emprego
• Inscrição: https://www.francetravail.fr
• Ajuda com CV, formação profissional e entrevistas

📌 **Reconhecimento de Diplomas (ENIC-NARIC)**
• Valide seus diplomas estrangeiros
• Facilita busca de emprego na sua área
• Site: https://www.france-education-international.fr

📌 **Mission Locale** (para jovens 16-25 anos)
• Acompanhamento personalizado
• Orientação profissional
• Ajuda na busca de emprego

💡 *Dica:* Consulte a página de serviços do app para encontrar organizações locais em Paris que podem ajudar!

🌐 Mais informações: https://refugies.info""",
        "links": ["https://www.francetravail.fr", "https://refugies.info"]
    },
    
    "housing": {
        "title": "🏠 Recursos para Moradia",
        "content": """Olá! Vi que você precisa de ajuda com moradia. Aqui estão informações importantes:

📌 **Urgência - Ligue 115 (SAMU Social)**
• Atendimento 24/7 gratuito
• Hébergement d'urgence (abrigo de emergência)
• Apenas ligue: 115

📌 **Logement Social (HLM)**
• Aluguel adaptado aos seus rendimentos
• Inscrição online possível
• Site: https://www.demande-logement-social.gouv.fr

📌 **Adoma**
• Soluções de habitação com aluguéis adaptados
• Especialmente para pessoas em reintegração

📌 **France Terre d'Asile**
• Centro de acolhimento para solicitantes de asilo
• 24 Rue Marc Seguin, 75018 Paris
• Tel: 01 53 04 39 99

💡 *Importante:* Se você está em situação de urgência, não hesite em ligar para o 115!

🌐 Mais informações: https://refugies.info""",
        "links": ["https://refugies.info", "https://www.demande-logement-social.gouv.fr"]
    },
    
    "legal": {
        "title": "⚖️ Recursos de Assistência Jurídica",
        "content": """Olá! Vejo que você precisa de ajuda jurídica. Aqui estão organizações especializadas:

📌 **La Cimade**
• Assistência jurídica gratuita para migrantes
• 176 Rue de Grenelle, 75007 Paris
• Tel: 01 40 08 05 34
• Horário: Ter-Qui 14h-18h

📌 **GISTI (Groupe d'Information)**
• Informações sobre direitos dos estrangeiros
• 3 Villa Marcès, 75011 Paris
• Tel: 01 43 14 84 84

📌 **Carte de Séjour**
• Renovação e solicitação online
• Site oficial: https://administration-etrangers-en-france.interieur.gouv.fr

📌 **OFPRA**
• Para questões de asilo e proteção
• Reunificação familiar

💡 *Dica:* Sempre leve cópias de todos os seus documentos importantes!

🌐 Mais informações: https://refugies.info""",
        "links": ["https://refugies.info", "https://administration-etrangers-en-france.interieur.gouv.fr"]
    },
    
    "health": {
        "title": "🏥 Recursos de Saúde",
        "content": """Olá! Vi que você precisa de ajuda com saúde. Aqui estão recursos importantes:

📌 **PASS (Permanence d'Accès aux Soins)**
• Atendimento médico gratuito
• Sem necessidade de cobertura de saúde
• Hôpital Saint-Louis, 1 Avenue Claude Vellefaux, 75010 Paris
• Tel: 01 42 49 49 49
• Horário: Seg-Sex 8h30-17h

📌 **Emergências**
• SAMU: 15 (emergências médicas)
• Urgências: vá ao hospital mais próximo
• Atendimento gratuito em emergências

📌 **AME (Aide Médicale d'État)**
• Cobertura de saúde para pessoas sem documentos
• Gratuita para quem não tem recursos

📌 **Dépistage MST**
• Testes gratuitos de doenças sexualmente transmissíveis
• Centros de saúde em toda Paris

💡 *Importante:* Em emergência, sempre vá ao hospital ou ligue 15!

🌐 Mais informações: https://refugies.info""",
        "links": ["https://refugies.info"]
    },
    
    "food": {
        "title": "🍽️ Recursos para Alimentação",
        "content": """Olá! Vi que você precisa de ajuda com alimentação. Aqui estão locais que podem ajudar:

📌 **Restaurants du Cœur**
• Refeições gratuitas
• 42 Rue Championnet, 75018 Paris
• Tel: 01 53 32 23 23
• Horário: Seg-Sex 11h30-13h30

📌 **Secours Catholique**
• Distribuição de alimentos
• 15 Rue de Maubeuge, 75009 Paris
• Tel: 01 45 49 73 00
• Horário: Seg-Sex 9h-17h

📌 **Croix-Rouge Française**
• Distribuição de alimentos e produtos de higiene
• 43 Rue de Valmy, 93100 Montreuil
• Tel: 01 48 51 96 00
• Horário: Qua e Sex 14h-17h

📌 **Banques Alimentaires**
• Distribuição de alimentos em toda França
• Diversos pontos em Paris

💡 *Dica:* Muitas associações também oferecem roupas e produtos de higiene!

🌐 Mais informações: https://refugies.info""",
        "links": ["https://refugies.info"]
    },
    
    "education": {
        "title": "📚 Recursos Educacionais",
        "content": """Olá! Vi que você precisa de ajuda com educação. Aqui estão recursos disponíveis:

📌 **CASNAV (Centre Académique)**
• Escolarização de crianças migrantes
• 12 Boulevard d'Indochine, 75019 Paris
• Tel: 01 44 62 39 36
• Horário: Seg-Sex 9h-17h

📌 **Universidades - Diplôme Universitaire**
• Programas especiais para refugiados
• Cursos gratuitos
• RÉSEAU MEnS

📌 **Reconhecimento de Diplomas**
• ENIC-NARIC para validação de diplomas estrangeiros
• Essencial para continuar estudos ou trabalhar

📌 **Bolsas e Apoio**
• Diversas universidades oferecem programas especiais
• Acompanhamento durante os estudos

💡 *Importante:* Todas as crianças têm direito à educação na França!

🌐 Mais informações: https://refugies.info""",
        "links": ["https://refugies.info", "https://www.france-education-international.fr"]
    },
    
    "social": {
        "title": "🤝 Recursos de Apoio Social",
        "content": """Olá! Vi que você precisa de apoio social. Aqui estão organizações que podem ajudar:

📌 **Emmaüs Solidarité**
• Apoio social e atividades comunitárias
• 4 Rue des Amandiers, 75020 Paris
• Tel: 01 43 58 24 52
• Horário: Seg-Sex 10h-18h

📌 **CAF (Caisses d'Allocations Familiales)**
• Ajuda financeira em diversas situações
• Inscrição e solicitação online
• Site: https://www.caf.fr

📌 **France Bénévolat**
• Oportunidades de voluntariado
• Valorizar suas competências
• Ganhar experiência local

📌 **Associations Locales**
• Atividades culturais e sociais
• Networking e integração

💡 *Dica:* Participar de atividades sociais ajuda muito na integração!

🌐 Mais informações: https://refugies.info""",
        "links": ["https://refugies.info", "https://www.caf.fr"]
    },
    
    "clothes": {
        "title": "👕 Recursos para Roupas e Vestuário",
        "content": """Olá! Vi que você precisa de roupas. Aqui estão locais que podem ajudar:

📌 **Croix-Rouge - Vestiaire**
• Distribuição gratuita de roupas
• 43 Rue de Valmy, 93100 Montreuil
• Tel: 01 48 51 96 00
• Horário: Qua e Sex 14h-17h

📌 **Emmaüs**
• Roupas a preços muito baixos ou gratuitas
• Diversos pontos em Paris
• Também móveis e utensílios

📌 **Secours Catholique**
• Vestiários sociais
• Distribuição gratuita para pessoas em necessidade

📌 **Associations de Quartier**
• Muitas associações de bairro têm vestiários
• Pergunte no centro social mais próximo

💡 *Dica:* Também oferece produtos de higiene e calçados!

🌐 Mais informações: https://refugies.info""",
        "links": ["https://refugies.info"]
    },
    
    "furniture": {
        "title": "🪑 Recursos para Móveis e Utensílios",
        "content": """Olá! Vi que você precisa de móveis. Aqui estão recursos disponíveis:

📌 **Emmaüs**
• Móveis a preços muito acessíveis
• Grande variedade de itens
• Diversos pontos em Paris

📌 **Ressourceries**
• Móveis de segunda mão
• Preços simbólicos
• Também eletrodomésticos

📌 **Associations Locales**
• Doações de móveis entre particulares
• Pergunte em centros sociais

📌 **Sites de Doação**
• Donnons.org
• Geev.com
• Grupos locais no Facebook

💡 *Dica:* Muitas pessoas doam móveis em bom estado quando se mudam!

🌐 Mais informações: https://refugies.info""",
        "links": ["https://refugies.info", "https://donnons.org"]
    },
    
    "transport": {
        "title": "🚗 Recursos para Transporte e Mobilidade",
        "content": """Olá! Vi que você precisa de ajuda com transporte. Aqui estão informações úteis:

📌 **Navigo (Passe de Transporte)**
• Tarifas reduzidas disponíveis
• Para quem recebe ajuda social
• Informações na RATP

📌 **Permis de Conduire (Carteira de Motorista)**
• Cours de français du code de la route
• Formação de 200h gratuita
• Réseau Mob'In France

📌 **Vélib' (Bicicletas Públicas)**
• Sistema de bicicletas compartilhadas
• Primeira meia hora gratuita
• Aplicativo Vélib'

📌 **Associations de Mobilité**
• Ajuda para locomoção
• Formações gratuitas

💡 *Dica:* Pergunte sobre tarifas sociais no transporte público!

🌐 Mais informações: https://refugies.info""",
        "links": ["https://refugies.info", "https://www.ratp.fr"]
    }
}

def get_auto_response(category: str) -> dict:
    """Retorna a resposta automática para uma categoria"""
    return AUTO_RESPONSES.get(category, None)

def format_auto_response_post(category: str, original_post_id: str) -> dict:
    """Formata a resposta automática como um post"""
    response = get_auto_response(category)
    if not response:
        return None
    
    return {
        "type": "offer",
        "category": category,
        "title": response["title"],
        "description": response["content"],
        "is_auto_response": True,
        "reply_to": original_post_id
    }
