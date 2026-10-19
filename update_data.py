import os
import sys
import json
import requests
from datetime import datetime, timedelta, timezone

# O Token não fica aqui! Ele vem do GitHub Actions Secrets por segurança.
TOKEN = os.environ.get("META_ACCESS_TOKEN")
BASE_URL = "https://graph.facebook.com/v21.0"

ACCOUNTS = {
    "act_947122467142147": "Autoclipper Live",
    "act_1447492070833917": "Douglas Souto (Reserva)",
}

RANGES = {"5d": 5, "7d": 7, "30d": 30, "all": None}

LEAD_TYPES = {
    "lead",
    "onsite_conversion.lead_grouped",
    "offsite_conversion.fb_pixel_lead",
}

if not TOKEN:
    print("ERRO: Token não encontrado nas variáveis de ambiente.")
    sys.exit(1)


def get_data(endpoint, params=None):
    params = dict(params or {})
    params["access_token"] = TOKEN
    resp = requests.get(f"{BASE_URL}/{endpoint}", params=params, timeout=60)
    body = resp.json()
    if "error" in body:
        print(f"AVISO: {endpoint}: {body['error'].get('message')}")
        return []
    return body.get("data", [])


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def leads_from(actions):
    # Usa o primeiro tipo de lead disponível para não duplicar contagem.
    found = {a.get("action_type"): num(a.get("value")) for a in (actions or [])}
    for t in ("lead", "offsite_conversion.fb_pixel_lead", "onsite_conversion.lead_grouped"):
        if t in found:
            return found[t]
    return 0.0


def norm(row):
    return {
        "spend": num(row.get("spend")),
        "impressions": int(num(row.get("impressions"))),
        "reach": int(num(row.get("reach"))),
        "clicks": int(num(row.get("inline_link_clicks"))),
        "leads": int(leads_from(row.get("actions"))),
    }


def time_params(days):
    if days is None:
        return {"date_preset": "maximum"}
    hoje = datetime.now(timezone.utc).date()
    inicio = hoje - timedelta(days=days - 1)
    return {"time_range": json.dumps({"since": inicio.isoformat(), "until": hoje.isoformat()})}


FIELDS = "spend,impressions,reach,inline_link_clicks,actions"

out = {"updated_at": datetime.now(timezone.utc).isoformat(), "accounts": {}}

for act_id, name in ACCOUNTS.items():
    acc = {"name": name, "ranges": {}}
    for key, days in RANGES.items():
        tp = time_params(days)
        total = get_data(f"{act_id}/insights", {**tp, "fields": FIELDS})
        placements = get_data(f"{act_id}/insights", {
            **tp, "fields": FIELDS,
            "breakdowns": "publisher_platform,platform_position", "limit": 200,
        })
        daily = []
        if days is not None:
            daily = get_data(f"{act_id}/insights", {
                **tp, "fields": FIELDS, "time_increment": 1, "limit": 100,
            })
        acc["ranges"][key] = {
            "total": norm(total[0]) if total else norm({}),
            "placements": [
                {**norm(r), "platform": r.get("publisher_platform"),
                 "position": r.get("platform_position")}
                for r in placements
            ],
            "daily": [{**norm(r), "date": r.get("date_start")} for r in daily],
        }
    out["accounts"][act_id] = acc

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2, ensure_ascii=False)

print("Dados do Meta Ads extraídos e salvos com sucesso em data.json!")
