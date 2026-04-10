import requests
import pandas as pd
import time

# =====================================================================
# REGRAS DO UNIVERSAL POKEMON RANDOMIZER
# =====================================================================
MUDANCAS_RANDOMIZER = {
    "Politoed": {"metodo": "Segurando Rei do Rock", "lvl": None},
    "Alakazam": {"metodo": "Level Up", "lvl": 37},
    "Machamp": {"metodo": "Level Up", "lvl": 37},
    "Golem": {"metodo": "Level Up", "lvl": 37},
    "Slowking": {"metodo": "Pedra Água", "lvl": None},
    "Magnezone": {"metodo": "Level Up", "lvl": 40},
    "Gengar": {"metodo": "Level Up", "lvl": 37},
    "Steelix": {"metodo": "Segurando Rev. Metálico", "lvl": None},
    "Rhyperior": {"metodo": "Segurando Protector", "lvl": None},
    "Kingdra": {"metodo": "Segurando Escama Dragão", "lvl": None},
    "Scizor": {"metodo": "Segurando Rev. Metálico", "lvl": None},
    "Electivire": {"metodo": "Segurando Electrizador", "lvl": None},
    "Magmortar": {"metodo": "Segurando Magmatizador", "lvl": None},
    "Leafeon": {"metodo": "Pedra Folha", "lvl": None},
    "Glaceon": {"metodo": "Pedra Alba", "lvl": None},
    "Porygon2": {"metodo": "Segurando Up-Grade", "lvl": None},
    "Porygon-z": {"metodo": "Segurando Discoxtranho", "lvl": None},
    "Probopass": {"metodo": "Level Up", "lvl": 40},
    "Milotic": {"metodo": "Level Up", "lvl": 35},
    "Dusknoir": {"metodo": "Segurando Traje Ceifador", "lvl": None},
    "Huntail": {"metodo": "Segurando Dente Mar.", "lvl": None},
    "Gorebyss": {"metodo": "Segurando Escama Mar.", "lvl": None},
    "Rhydon": {"metodo": "Level Up", "lvl": 30},
    "Seadra": {"metodo": "Level Up", "lvl": 30},
    "Dragonite": {"metodo": "Level Up", "lvl": 40},
    "Piloswine": {"metodo": "Level Up", "lvl": 30},
    "Tyranitar": {"metodo": "Level Up", "lvl": 40},
    "Lairon": {"metodo": "Level Up", "lvl": 30},
    "Aggron": {"metodo": "Level Up", "lvl": 40},
    "Vibrava": {"metodo": "Level Up", "lvl": 30},
    "Flygon": {"metodo": "Level Up", "lvl": 40},
    "Dusclops": {"metodo": "Level Up", "lvl": 30},
    "Glalie": {"metodo": "Level Up", "lvl": 40},
    "Sealeo": {"metodo": "Level Up", "lvl": 30},
    "Walrein": {"metodo": "Level Up", "lvl": 40},
    "Salamence": {"metodo": "Level Up", "lvl": 40},
    "Metagross": {"metodo": "Level Up", "lvl": 40},
    "Garchomp": {"metodo": "Level Up", "lvl": 40},
    "Mantine": {"metodo": "Level Up", "lvl": 35},
    "Espeon": {"metodo": "Pedra Solar", "lvl": None},
    "Umbreon": {"metodo": "Pedra Lunar", "lvl": None},
    "Gliscor": {"metodo": "Segurando Presa Afiada", "lvl": None},
    "Weavile": {"metodo": "Segurando Garra Afiada", "lvl": None},
    "Roselia": {"metodo": "Felicidade (160)", "lvl": None},
    "Chimecho": {"metodo": "Felicidade (160)", "lvl": None},
    "Chansey": {"metodo": "Segurando Pedra Oval", "lvl": None},
    "Lucario": {"metodo": "Felicidade (160)", "lvl": None},
}

def obter_dados(url):
    try:
        r = requests.get(url)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None

def extrair_golpes_hgss(pid):
    dados = obter_dados(f"https://pokeapi.co/api/v2/pokemon/{pid}")
    golpes = {}
    lvl_maximo = 0
    # Usamos um set para contar golpes únicos no lvl 1 sem repetições da API
    golpes_lvl1_brutos = set()
    
    if dados:
        for move in dados['moves']:
            nome_golpe = move['move']['name'].title().replace("-", " ")
            for detalhe in move['version_group_details']:
                if detalhe['version_group']['name'] == 'heartgold-soulsilver' and detalhe['move_learn_method']['name'] == 'level-up':
                    lvl = detalhe['level_learned_at']
                    if lvl > 0:
                        # REGISTRA PARA O AVISO (Antes da conversão/filtragem de maior level)
                        if lvl == 1:
                            golpes_lvl1_brutos.add(nome_golpe)
                            
                        # MANTÉM A CONVERSÃO (Filtragem para a planilha: maior level ganha)
                        if nome_golpe not in golpes or lvl > golpes[nome_golpe]:
                            golpes[nome_golpe] = lvl
                        if lvl > lvl_maximo:
                            lvl_maximo = lvl
                            
    return golpes, lvl_maximo, len(golpes_lvl1_brutos)

def extrair_todos_ids(node):
    ids = [int(node['species']['url'].split('/')[-2])]
    for child in node['evolves_to']:
        ids.extend(extrair_todos_ids(child))
    return ids

def get_paths(node):
    if not node['evolves_to']:
        return [[node]]
    paths = []
    for child in node['evolves_to']:
        for subpath in get_paths(child):
            paths.append([node] + subpath)
    return paths

def principal():
    ids_para_testar = range(1, 494)
    
    linhas_planilha = []
    vistos = set()
    familias_processadas = set()
    
    def add_linha(linha_array):
        t = tuple(linha_array)
        if t not in vistos:
            vistos.add(t)
            linhas_planilha.append(linha_array)

    add_linha(["ID", "Pokemon", "Lvl", "Atividade", "Golpe&Itens", "OBS"])
    
    print("Iniciando mapeamento...")
    
    for i in ids_para_testar:
        if i in familias_processadas:
            continue
            
        especie = obter_dados(f"https://pokeapi.co/api/v2/pokemon-species/{i}")
        if not especie: continue
        
        chain_url = especie['evolution_chain']['url']
        chain = obter_dados(chain_url)
        if not chain: continue
        
        todos_ids = extrair_todos_ids(chain['chain'])
        min_id_familia = min(todos_ids)
        
        caminhos = get_paths(chain['chain'])
        
        for caminho in caminhos:
            linha_evolutiva = []
            
            for idx, n in enumerate(caminho):
                nome = n['species']['name'].capitalize()
                pid = int(n['species']['url'].split('/')[-2])
                familias_processadas.add(pid)
                
                if pid > 493: continue
                
                # CORREÇÃO: Gerando ID como número (float) para o Excel não reclamar
                novo_id_formatado = float(f"{min_id_familia}.{idx}")
                
                min_lvl = None
                metodo_str = "Base"
                
                if idx > 0:
                    if nome in MUDANCAS_RANDOMIZER:
                        regra = MUDANCAS_RANDOMIZER[nome]
                        metodo_str = regra['metodo']
                        min_lvl = regra['lvl']
                    elif len(n['evolution_details']) > 0:
                        detalhes = n['evolution_details'][0]
                        trigger = detalhes['trigger']['name']
                        if trigger == 'level-up':
                            min_lvl = detalhes.get('min_level')
                            if min_lvl:
                                metodo_str = "Normal"
                            elif detalhes.get('min_happiness'):
                                metodo_str = "Felicidade (160)"
                            else:
                                metodo_str = "Cond. Especial"
                        elif trigger == 'use-item':
                            metodo_str = detalhes['item']['name'].title().replace('-', ' ')
                        elif trigger == 'trade':
                            metodo_str = "Troca"
                    else:
                        metodo_str = "Nasce de Ovo / Misterioso"
                
                # Agora recebemos a contagem real de golpes de nível 1
                golpes, lvl_max, qtd_lvl1_real = extrair_golpes_hgss(pid)
                
                linha_evolutiva.append({
                    'id': novo_id_formatado, 'nome': nome, 'min_lvl': min_lvl,
                    'metodo_str': metodo_str, 'golpes': golpes, 'lvl_maximo': lvl_max,
                    'qtd_lvl1_real': qtd_lvl1_real
                })
                
            for idx in range(len(linha_evolutiva)):
                membro = linha_evolutiva[idx]
                
                if membro['lvl_maximo'] > 0:
                    add_linha([membro['id'], membro['nome'], membro['lvl_maximo'], "Ultimo Golpe", "", ""])
                    
                if idx < len(linha_evolutiva) - 1:
                    prox = linha_evolutiva[idx+1]
                    lvl_evolucao = prox['min_lvl'] if prox['min_lvl'] is not None else 1
                    obs = f"Evolui para {prox['nome']}"
                    add_linha([membro['id'], membro['nome'], lvl_evolucao, "Evoluir", prox['metodo_str'], obs])

                # AGORA O AVISO USA A CONTAGEM REAL (Antes da filtragem de level)
                if membro['qtd_lvl1_real'] >= 5:
                    add_linha([membro['id'], membro['nome'], 1, "Aviso", "Muitos golpes base", f"Atenção: Aprende {membro['qtd_lvl1_real']} golpes no level 1!"])

                for nome_golpe, lvl_golpe in membro['golpes'].items():
                    parentes_que_nao_aprendem = []
                    
                    for outro_membro in linha_evolutiva:
                        if outro_membro['nome'] != membro['nome']:
                            if nome_golpe not in outro_membro['golpes']:
                                parentes_que_nao_aprendem.append(outro_membro['nome'])
                    
                    if len(parentes_que_nao_aprendem) > 0:
                        nomes_formatados = ", ".join(parentes_que_nao_aprendem)
                        obs = f"Na família, não é aprendido por: {nomes_formatados}"
                        add_linha([membro['id'], membro['nome'], lvl_golpe, "Aprender", nome_golpe, obs])

        if i % 15 == 0:
            print(f"Progresso: {i}/493 Pokémon analisados...")
            time.sleep(0.5)

    print("Gerando arquivo Excel...")
    df = pd.DataFrame(linhas_planilha[1:], columns=linhas_planilha[0])
    nome_arquivo = 'pokemon_randomizer_com_golpes.xlsx'
    df.to_excel(nome_arquivo, index=False)
        
    print(f"Concluído! Arquivo '{nome_arquivo}' criado. IDs agora são números e Blastoise terá seu aviso!")

if __name__ == "__main__":
    principal()