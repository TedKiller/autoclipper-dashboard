import os
import requests
import json
from datetime import datetime, timedelta

# O Token não fica aqui! Ele vem do GitHub Actions Secrets por segurança.
TOKEN = os.environ.get("META_ACCESS_TOKEN")
ACT_ID = "act_947122467142147"
BASE_URL = "https://graph.facebook.com/v21.0"

if not TOKEN:
    print("ERRO: Token não encontrado nas variáveis de ambiente.")
    exit(1)

# Calcula os últimos 5 dias automaticamente
hoje = datetime.utcnow().date()
cinco_dias_atras = hoje - timedelta(days=5)

time_range = json.dumps({
    'since': cinco_dias_atras.strftime('%Y-%m-%d'),
    'until': hoje.strftime('%Y-%m-%d')
})

def get_data(endpoint, params=None):
    if params is None:
        params = {}
    params['access_token'] = TOKEN
    url = f"{BASE_URL}/{endpoint}"
    resp = requests.get(url, params=params)
    return resp.json()

data_5d = {}

# Total dos 5 dias
data_5d['total_5d'] = get_data(f"{ACT_ID}/insights", {
    'time_range': time_range,
    'fields': 'spend,impressions,clicks,cpc,cpm,ctr,reach,actions,inline_link_clicks'
})

# Por dia
data_5d['daily_5d'] = get_data(f"{ACT_ID}/insights", {
    'time_range': time_range,
    'time_increment': 1,
    'fields': 'spend,impressions,clicks,cpc,ctr,reach'
})

# Por plataforma (Instagram vs Facebook)
data_5d['by_platform_5d'] = get_data(f"{ACT_ID}/insights", {
    'time_range': time_range,
    'breakdowns': 'publisher_platform',
    'fields': 'spend,impressions,clicks,cpc,ctr'
})

# Salva em um arquivo JSON que a página vai ler
with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(data_5d, f, indent=2, ensure_ascii=False)

print("Dados do Meta Ads extraídos e salvos com sucesso em data.json!")
