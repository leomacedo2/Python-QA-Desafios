import requests
import time

# Dicionários de Cores e Emojis
TABELA_TIPOS = {
    'Normal':   ('\033[97m', '⚪'), 
    'Fire':     ('\033[91m', '🔥'), 
    'Water':    ('\033[94m', '💧'), 
    'Grass':    ('\033[92m', '🌿'), 
    'Electric': ('\033[93m', '⚡'), 
    'Ice':      ('\033[96m', '❄️'), 
    'Fighting': ('\033[31m', '🥊'), 
    'Poison':   ('\033[35m', '☠️'),  
    'Ground':   ('\033[33m', '🏜️'),  
    'Flying':   ('\033[36m', '🌪️'),  
    'Psychic':  ('\033[95m', '🔮'), 
    'Bug':      ('\033[32m', '🐛'), 
    'Rock':     ('\033[90m', '🪨'), 
    'Ghost':    ('\033[34m', '👻'), 
    'Dragon':   ('\033[34m', '🐉'), 
    'Dark':     ('\033[90m', '🌙'), 
    'Steel':    ('\033[37m', '⚙️'), 
}

CATEGORIA_GOLPE = {
    'physical': ('\033[91m', '💥', 'Físico'),
    'special':  ('\033[96m', '🌀', 'Especial'),
    'status':   ('\033[90m', '🛡️', 'Status')
}

METODOS_EMOJI = {
    'level-up': '📈 Nível',
    'machine': '💿 TM/HM',
    'egg': '🥚 Ovo',
    'tutor': '👨‍🏫 Tutor',
    'light-ball-egg': '⚡ Ovo Especial'
}

RESET_COR = '\033[0m'

# Mapeamento estrito das gerações para a Máquina do Tempo
GEN_VERSIONS = {
    'red-blue': 1.0, 'yellow': 1.1,
    'gold-silver': 2.0, 'crystal': 2.1,
    'ruby-sapphire': 3.0, 'emerald': 3.1, 'firered-leafgreen': 3.2,
    'diamond-pearl': 4.0, 'platinum': 4.1, 'heartgold-soulsilver': 4.2,
    'black-white': 5.0, 'black-2-white-2': 5.1,
    'x-y': 6.0, 'omega-ruby-alpha-sapphire': 6.1,
    'sun-moon': 7.0, 'ultra-sun-ultra-moon': 7.1, 
    'lets-go-pikachu-lets-go-eevee': 7.2, 
    'sword-shield': 8.0, 'brilliant-diamond-and-shining-pearl': 8.1, 'legends-arceus': 8.2,
    'scarlet-violet': 9.0
}

GEN_NOME_PARA_NUM = {
    'generation-i': 1, 'generation-ii': 2, 'generation-iii': 3,
    'generation-iv': 4, 'generation-v': 5, 'generation-vi': 6,
    'generation-vii': 7, 'generation-viii': 8, 'generation-ix': 9
}

def buscar_golpes_linhagem_hgss(pokemon_id):
    print(f"\n🔍 Iniciando busca pelo Pokémon ID: {pokemon_id} em HeartGold/SoulSilver...")
    
    linhagem = []
    especie_atual = str(pokemon_id)
    
    # 1. Traçar a árvore genealógica de trás para frente (Até Gen 4)
    try:
        url_poke = f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}"
        resp_poke = requests.get(url_poke)
        if resp_poke.status_code != 200:
            print("❌ Pokémon não encontrado! Verifique o ID.")
            return
        
        dados_iniciais = resp_poke.json()
        url_species = dados_iniciais['species']['url'] 
        resp_species = requests.get(url_species).json()
        especie_atual = resp_species['name']
        
        if str(pokemon_id) != str(resp_species['id']):
            linhagem.append(dados_iniciais['name'])
            
    except Exception as e:
        print(f"❌ Erro ao buscar dados iniciais: {e}")
        return

    while especie_atual:
        url_species = f"https://pokeapi.co/api/v2/pokemon-species/{especie_atual}"
        resp = requests.get(url_species)
        if resp.status_code != 200: break
            
        dados_especie = resp.json()
        if dados_especie['name'] not in linhagem:
            linhagem.append(dados_especie['name'])
        
        preevolucao = dados_especie.get('evolves_from_species')
        if preevolucao:
            resp_pre = requests.get(preevolucao['url']).json()
            gen_pre = GEN_NOME_PARA_NUM.get(resp_pre['generation']['name'], 99)
            
            if gen_pre <= 4:
                especie_atual = preevolucao['name']
            else:
                especie_atual = None
        else:
            especie_atual = None

    print(f"🧬 Linhagem encontrada: {' <- '.join(linhagem).title()}")
    
    # 2. Coletar golpes HGSS
    golpes_dict = {} 
    for poke in linhagem:
        url_poke = f"https://pokeapi.co/api/v2/pokemon/{poke}"
        resp_req = requests.get(url_poke)
        
        if resp_req.status_code != 200:
            url_alternativa = f"https://pokeapi.co/api/v2/pokemon/{poke}-normal"
            resp_req = requests.get(url_alternativa)
            if resp_req.status_code != 200:
                print(f"   ⚠️ Aviso: Ignorando dados de linhagem inconsistentes para '{poke}'.")
                continue
                
        resp_poke = resp_req.json()
        
        for move_data in resp_poke['moves']:
            nome_golpe = move_data['move']['name']
            for detail in move_data['version_group_details']:
                if detail['version_group']['name'] == 'heartgold-soulsilver':
                    metodo = detail['move_learn_method']['name']
                    if nome_golpe not in golpes_dict:
                        golpes_dict[nome_golpe] = set()
                    golpes_dict[nome_golpe].add(metodo)
                
    if not golpes_dict:
        print("⚠️ Nenhum golpe encontrado para este Pokémon na Geração 4.")
        return

    # 3. Baixar dados técnicos
    print(f"📡 Baixando dados técnicos de {len(golpes_dict)} golpes únicos de HGSS...")
    
    lista_bruta = []
    total_golpes = len(golpes_dict)
    
    for i, (nome_golpe, metodos) in enumerate(golpes_dict.items(), 1):
        if i % 20 == 0:
            print(f"   ⏳ Analisando golpe {i}/{total_golpes}...")
            
        try:
            resp_move = requests.get(f"https://pokeapi.co/api/v2/move/{nome_golpe}").json()
            
            tipo_golpe = resp_move['type']['name'].title()
            power_val = resp_move.get('power') if resp_move.get('power') is not None else 0
            accuracy_str = str(resp_move.get('accuracy')) if resp_move.get('accuracy') is not None else '-'
            pp_str = str(resp_move.get('pp')) if resp_move.get('pp') is not None else '-'
            
            categoria_raw = resp_move.get('damage_class', {}).get('name', 'status')
            
            past_values = resp_move.get('past_values', [])
            past_values.sort(key=lambda x: GEN_VERSIONS.get(x['version_group']['name'], 99.0), reverse=True)
            
            for past in past_values:
                gen_mudanca = GEN_VERSIONS.get(past['version_group']['name'], 99.0)
                
                if gen_mudanca > 4.2:
                    if past.get('power') is not None: power_val = past['power']
                    if past.get('accuracy') is not None: accuracy_str = str(past['accuracy'])
                    if past.get('pp') is not None: pp_str = str(past['pp'])
                    if past.get('type') is not None: tipo_golpe = past['type']['name'].title()
            
            # Formatando os métodos com os Emojis
            metodos_formatados = [METODOS_EMOJI.get(m, f"🔹 {m.title()}") for m in sorted(metodos)]
            metodos_str = ", ".join(metodos_formatados)
            
            lista_bruta.append({
                'nome': nome_golpe.title().replace('-', ' '),
                'tipo': tipo_golpe,
                'categoria': categoria_raw,
                'metodos': metodos_str,
                'power': power_val,
                'accuracy': accuracy_str,
                'pp': pp_str
            })
        except Exception:
            pass 
        time.sleep(0.05) 

    # 4. Ordenação por Força e Tipo
    forca_maxima_por_tipo = {}
    golpes_por_tipo = {}
    
    for g in lista_bruta:
        tipo = g['tipo']
        if tipo not in golpes_por_tipo: golpes_por_tipo[tipo] = []
        golpes_por_tipo[tipo].append(g)
        if tipo not in forca_maxima_por_tipo or g['power'] > forca_maxima_por_tipo[tipo]:
            forca_maxima_por_tipo[tipo] = g['power']

    tipos_ordenados = sorted(forca_maxima_por_tipo.keys(), key=lambda t: forca_maxima_por_tipo[t], reverse=True)

    lista_final = []
    for tipo in tipos_ordenados:
        golpes_deste_tipo = sorted(golpes_por_tipo[tipo], key=lambda x: x['power'], reverse=True)
        lista_final.extend(golpes_deste_tipo)

    # 5. Impressão
    print("\n" + "="*133)
    # Aumentei o espaçamento da coluna MÉTODO(S) para comportar os emojis sem quebrar a tabela
    print(f"{'NOME DO GOLPE':<18} | {'TIPO':<11} | {'CATEGORIA':<12} | {'MÉTODO(S)':<45} | {'FORÇA':<6} | {'ACURÁCIA':<8} | {'PP':<4}")
    print("="*133)
    
    for g in lista_final:
        forca_exibicao = str(g['power']) if g['power'] > 0 else '-'
        
        # Formatando Tipo
        cor_tipo, emoji_tipo = TABELA_TIPOS.get(g['tipo'], ('\033[37m', '✨'))
        tipo_formatado = f"{cor_tipo}{emoji_tipo} {g['tipo']:<8}{RESET_COR}"
        
        # Formatando Categoria
        cor_cat, emoji_cat, nome_cat = CATEGORIA_GOLPE.get(g['categoria'], ('\033[37m', '✨', '???'))
        cat_formatada = f"{cor_cat}{emoji_cat} {nome_cat:<8}{RESET_COR}"
        
        print(f"{g['nome']:<18} | {tipo_formatado} | {cat_formatada} | {g['metodos']:<45} | {forca_exibicao:<6} | {g['accuracy']:<8} | {g['pp']:<4}")
    print("="*133)

if __name__ == "__main__":
    print("Bem-vindo ao Analisador de Movesets HeartGold/SoulSilver (Versão Emoji)!")
    while True:
        entrada = input("\nDigite o ID numérico do Pokémon (ou digite 'sair' para encerrar): ")
        if entrada.lower() == 'sair': break
        if not entrada.isdigit():
            print("❌ Por favor, digite apenas números válidos.")
            continue
        buscar_golpes_linhagem_hgss(int(entrada))