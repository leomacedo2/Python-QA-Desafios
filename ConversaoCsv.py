import pandas as pd

def converter_csv(arquivo_entrada, arquivo_saida, separador_origem, separador_destino):
    try:
        # Carrega o arquivo
        df = pd.read_csv(arquivo_entrada, sep=separador_origem, encoding='utf-8')
        
        # Salva com o novo separador
        df.to_csv(arquivo_saida, sep=separador_destino, index=False, encoding='utf-8')
        print(f"Sucesso! Arquivo salvo como: {arquivo_saida}")
    except Exception as e:
        print(f"Erro: {e}")

# --- COMO USAR ---

# 1. Para deixar fácil de abrir no Excel BR (Vírgula -> Ponto e Vírgula)
# converter_csv('golpes.csv', 'golpes_para_editar.csv', ',', ';')

# 2. Para voltar ao padrão do Randomizer (Ponto e Vírgula -> Vírgula)
converter_csv('golpes_para_editar.csv', 'golpes_pronto.csv', ';', ',')