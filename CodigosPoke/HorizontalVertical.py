import pandas as pd

def verticalizar(arquivo_entrada, arquivo_saida_excel):
    # Lendo o CSV original (separado por vírgula)
    # Usamos header=None primeiro para tratar os nomes das colunas duplicadas
    df = pd.read_csv(arquivo_entrada, sep=',', encoding='utf-8')
    
    id_vars = ['ID', 'Name']
    cols = df.columns.difference(id_vars)
    
    lista_vertical = []
    
    # Percorre cada linha (Pokémon)
    for _, row in df.iterrows():
        # Agrupa os golpes de 2 em 2 (Move e Lvl)
        for i in range(2, len(df.columns), 2):
            move = row.iloc[i]
            lvl = row.iloc[i+1]
            # Só adiciona se o golpe não for '0' ou vazio
            if pd.notna(move) and str(move) != '0':
                lista_vertical.append({
                    'ID': row['ID'],
                    'Name': row['Name'],
                    'Move': move,
                    'Lvl': lvl
                })
    
    df_vertical = pd.DataFrame(lista_vertical)
    df_vertical.to_excel(arquivo_saida_excel, index=False)
    print(f"Arquivo vertical pronto para editar: {arquivo_saida_excel}")

def horizontalizar(arquivo_excel_editado, arquivo_csv_final):
    df_vert = pd.read_excel(arquivo_excel_editado)
    
    # Agrupa de volta por ID e Nome
    pokemons = df_vert.groupby(['ID', 'Name'])
    
    linhas_horizontais = []
    max_golpes = 20 # O padrão do seu CSV parece ter espaço para muitos golpes
    
    for (pid, name), group in pokemons:
        linha = [pid, name]
        golpes_atuais = group[['Move', 'Lvl']].values.flatten().tolist()
        
        # Preenche com 0 o que sobrar para manter o tamanho do arquivo original
        total_colunas_necessarias = max_golpes * 2
        golpes_atuais.extend([0] * (total_colunas_necessarias - len(golpes_atuais)))
        
        linha.extend(golpes_atuais[:total_colunas_necessarias])
        linhas_horizontais.append(linha)
    
    # Cria os nomes das colunas no padrão Move, Lvl, Move, Lvl...
    headers = ['ID', 'Name']
    for i in range(max_golpes):
        headers.extend(['Move', 'Lvl'])
        
    df_final = pd.DataFrame(linhas_horizontais, columns=headers)
    df_final.to_csv(arquivo_csv_final, index=False, sep=',', encoding='utf-8')
    print(f"Arquivo convertido para o Randomizer: {arquivo_csv_final}")

# --- EXECUÇÃO ---
# verticalizar('golpes.csv', 'editar_aqui.xlsx')
horizontalizar('editar_aqui.xlsx', 'golpes_pronto.csv')