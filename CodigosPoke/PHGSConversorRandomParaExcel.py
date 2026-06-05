import pandas as pd
import re

# Caminhos dos arquivos baseados no seu diretório
arquivo_txt = r"C:\Leo\Emuladores\NDS\Log_Oficial.txt"
arquivo_excel = r"C:\Leo\Emuladores\NDS\SoulSilverOficial.xlsx"

dados_finais = []
linha_atual = []

print("Lendo o arquivo e extraindo os dados...")

# Tentamos abrir com utf-8-sig (que remove automaticamente o caractere invisível BOM)
try:
    with open(arquivo_txt, 'r', encoding='utf-8-sig') as f:
        linhas = f.readlines()
except UnicodeDecodeError:
    # Se der erro, tenta com latin-1
    with open(arquivo_txt, 'r', encoding='latin-1') as f:
        linhas = f.readlines()

for linha in linhas:
    linha = linha.strip()
    
    # Pula linhas vazias
    if not linha:
        continue
    
    # 1. Verifica se é a linha de cabeçalho (Ex: "Area #1 - Vila Primavera Surfing (rate=15)")
    match_cabecalho = re.match(r"^Area #(\d+)\s+-\s+(.*)", linha)
    if match_cabecalho:
        # Se já tínhamos um Set montado, adiciona ele à nossa lista final
        if linha_atual:
            dados_finais.append(linha_atual)
        
        # Cria a base da nova linha com a [ID, Local]
        id_set = int(match_cabecalho.group(1))
        local = match_cabecalho.group(2).strip()
        linha_atual = [id_set, local]
        continue
        
    # 2. Como o formato mudou e não tem mais "HP", qualquer linha que não seja 
    # cabeçalho (e não esteja vazia) é um Pokémon com seu respectivo Level.
    if linha_atual:
        linha_atual.append(linha)

# Não esquecer de adicionar o último Set do arquivo
if linha_atual:
    dados_finais.append(linha_atual)

# 3. Preparando para o Excel
# Descobre qual Set teve o maior número de Pokémon para criar a quantidade certa de colunas
max_colunas = max(len(linha) for linha in dados_finais)

# Cria os cabeçalhos: "ID", "Local", "Slot 1", "Slot 2", etc.
nomes_colunas = ["ID", "Local"] + [f"Slot {i+1}" for i in range(max_colunas - 2)]

print("Gerando a planilha...")

# Cria a tabela usando o Pandas e salva em Excel
df = pd.DataFrame(dados_finais, columns=nomes_colunas)
df.to_excel(arquivo_excel, index=False)

print(f"Sucesso! Sua planilha foi criada em: {arquivo_excel}")