import csv

def formatar_planilha():
    linhas_originais = []
    # Lê o arquivo bruto que geramos com a PokeAPI
    with open('pokemon_randomizer_com_golpes.csv', 'r', encoding='utf-8-sig') as f:
        leitor = csv.DictReader(f, delimiter=';') 
        for row in leitor:
            linhas_originais.append(row)

    pokemons = {}
    ordem_pokemons = []

    # Organiza os dados
    for row in linhas_originais:
        nome = row['Pokemon']
        if nome not in pokemons:
            pokemons[nome] = {'evolucao': None, 'golpes': [], 'ultimo_golpe': 0}
            ordem_pokemons.append(nome)

        ativ = row['Atividade']
        try:
            lvl = int(row['Lvl']) if row['Lvl'] else 0
        except ValueError:
            lvl = 0

        if ativ == 'Evoluir':
            pokemons[nome]['evolucao'] = row
        elif ativ == 'Aprender':
            pokemons[nome]['golpes'].append({'nome_golpe': row['Golpe&Itens'], 'lvl_original': lvl})
        elif ativ == 'Ultimo Golpe':
            pokemons[nome]['ultimo_golpe'] = lvl

    linhas_formatadas = []
    contador_id = 1
    nivel_evolucao_atual = 1

    # Aplica a "Regra da Escadinha"
    for nome in ordem_pokemons:
        dados = pokemons[nome]
        
        # O nível base para aprender golpes novos começa 1 level APÓS a evolução
        lvl_base = nivel_evolucao_atual + 1

        golpes_ordenados = sorted(dados['golpes'], key=lambda x: x['lvl_original'])

        for golpe in golpes_ordenados:
            # O golpe vai ser no level original DELE, ou no lvl_base atual (o que for maior)
            lvl_aplicado = max(lvl_base, golpe['lvl_original'])
            
            linhas_formatadas.append([
                contador_id, nome, lvl_aplicado, 'Aprender', golpe['nome_golpe'], ''
            ])
            contador_id += 1
            # Sobe o degrau da escada para o próximo golpe não chocar
            lvl_base = lvl_aplicado + 1

        if dados['ultimo_golpe'] > 0:
            lvl_ultimo = max(lvl_base, dados['ultimo_golpe'])
            linhas_formatadas.append([
                contador_id, nome, lvl_ultimo, 'Ultimo Golpe', '', ''
            ])
            contador_id += 1
            lvl_base = lvl_ultimo + 1

        evo = dados['evolucao']
        if evo:
            try:
                lvl_evo = int(evo['Lvl'])
            except ValueError:
                # Se for evolução por pedra/felicidade que não tem level definido, 
                # a gente joga pro final da escadinha atual
                lvl_evo = lvl_base 
                
            linhas_formatadas.append([
                contador_id, nome, lvl_evo, 'Evoluir', evo['Golpe&Itens'], evo['OBS']
            ])
            contador_id += 1
            nivel_evolucao_atual = lvl_evo
        else:
            # Reseta a escadinha para a próxima família
            nivel_evolucao_atual = 1

    # Salva o arquivo final com IDs limpos
    with open('SoulSilver_Automated.csv', 'w', newline='', encoding='utf-8-sig') as f:
        escritor = csv.writer(f, delimiter=';')
        escritor.writerow(['ID', 'Pokemon', 'Lvl', 'Atividade', 'Golpe&Itens', 'OBS'])
        escritor.writerows(linhas_formatadas)
        
    print("Planilha automatizada com sucesso! Seus dias de trabalho escravo acabaram.")

if __name__ == "__main__":
    formatar_planilha()