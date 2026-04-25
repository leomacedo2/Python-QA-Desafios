import requests
from openpyxl import Workbook

BASE_URL = "https://pokeapi.co/api/v2"

# Filtro exato e cirúrgico:
# Adicionado "fairy" para bloquear o Arceus-Fairy (Gen 6).
TERMOS_BLOQUEADOS = {
    "mega", "gmax", "alola", "galar", "hisui", "paldea", 
    "primal", "totem", "eternamax", "cap", "cosplay", 
    "star", "belle", "phd", "libre", "starter", "stellar", "fairy"
}

def format_evolution_details(details):
    if not details:
        return "Desconhecido"
    
    d = details[0]
    parts = []

    trigger_name = d.get("trigger", {}).get("name") if d.get("trigger") else None
    
    if trigger_name == "level-up":
        parts.append("Level")
    elif trigger_name == "trade":
        parts.append("Troca")
    elif trigger_name == "use-item":
        parts.append("Usar item")

    if d.get("min_level"): parts.append(f"{d['min_level']}")
    if d.get("item"): parts.append(f"{d['item']['name'].replace('-', ' ')}")
    if d.get("held_item"): parts.append(f"Segurando {d['held_item']['name'].replace('-', ' ')}")
    if d.get("time_of_day"): parts.append(f"De {d['time_of_day']}")
    if d.get("min_happiness"): parts.append("Felicidade alta")
    if d.get("location"): parts.append(f"Em {d['location']['name'].replace('-', ' ')}")
    if d.get("known_move"): parts.append(f"Sabendo {d['known_move']['name'].replace('-', ' ')}")

    if not parts:
        return trigger_name.capitalize() if trigger_name else "Condição especial"
    
    return " + ".join(parts).title()

def extract_multiple_evolutions(chain, results, valid_names):
    name = chain["species"]["name"]
    
    if name not in valid_names:
        return

    valid_evolutions = [evo for evo in chain["evolves_to"] if evo["species"]["name"] in valid_names]

    if len(valid_evolutions) > 1:
        evo_descriptions = []
        for evo in valid_evolutions:
            evo_name = evo["species"]["name"].capitalize()
            method = format_evolution_details(evo.get("evolution_details", []))
            evo_descriptions.append(f"{evo_name} ({method})")

        results.append({
            "pokemon": name.capitalize(),
            "method": "Evolução Múltipla",
            "quantidade": len(valid_evolutions),
            "evolutions": " | ".join(evo_descriptions)
        })

    for evo in valid_evolutions:
        extract_multiple_evolutions(evo, results, valid_names)

def main():
    session = requests.Session()
    
    print("Iniciando o download da lista base de Pokémon...")
    species_list = session.get(f"{BASE_URL}/pokemon-species?limit=493").json()["results"]
    
    valid_names = set(p["name"] for p in species_list)

    wb = Workbook()
    ws = wb.active
    ws.title = "Pokemons Especiais"
    ws.append(["ID", "Pokemon Base", "Categoria", "Quantidade", "Detalhes (Evoluções ou Formas)"])

    processed_chains = set()

    print("\nVasculhando a PokéAPI com lupa... (Aguarde um instante)\n")

    for i, species in enumerate(species_list, start=1):
        name = species["name"]
        
        if i % 50 == 0 or i == 493:
            print(f"[*] Analisando Pokémon {i}/493 ({name.capitalize()})...")

        try:
            species_data = session.get(species["url"]).json()
            
            # --- O SEGREDO REVELADO: BUSCA POR FORMAS ---
            valid_forms = []
            
            for v in species_data.get("varieties", []):
                # O Pulo do Gato: Acessa os dados específicos do Pokémon para descobrir as formas escondidas
                poke_data = session.get(v["pokemon"]["url"]).json()
                
                for f in poke_data.get("forms", []):
                    form_name = f["name"]
                    # Corta o nome em partes (ex: "arceus-dark" vira ["arceus", "dark"])
                    parts = form_name.split('-')
                    
                    # Filtro exato: só bloqueia se a palavra exata existir na lista proibida
                    if not any(termo in parts for termo in TERMOS_BLOQUEADOS):
                        valid_forms.append(form_name)

            # Limpa qualquer forma duplicada que a API possa ter mandado
            valid_forms = list(dict.fromkeys(valid_forms))

            if len(valid_forms) > 1:
                forms_str = [f.replace("-", " ").title() for f in valid_forms]
                ws.append([i, name.capitalize(), "Possui Formas", len(forms_str), " | ".join(forms_str)])

            # --- PROCESSAMENTO DE EVOLUÇÕES ---
            evo_chain_dict = species_data.get("evolution_chain")
            evo_chain_url = evo_chain_dict.get("url") if isinstance(evo_chain_dict, dict) else None

            if evo_chain_url and evo_chain_url not in processed_chains:
                processed_chains.add(evo_chain_url)
                chain_data = session.get(evo_chain_url).json()
                
                results = []
                extract_multiple_evolutions(chain_data["chain"], results, valid_names)
                
                for r in results:
                    ws.append([i, r["pokemon"], r["method"], r["quantidade"], r["evolutions"]])
                    
        except Exception as e:
            print(f"Erro inesperado no pokemon {name}: {e}")

    nome_arquivo = "pokemons_definitivo_agora_vai.xlsx"
    wb.save(nome_arquivo)
    print(f"\nFeito! O arquivo '{nome_arquivo}' foi gerado.")

if __name__ == "__main__":
    main()