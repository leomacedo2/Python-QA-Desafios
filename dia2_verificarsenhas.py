import re

lista_senhas = []

# Coletando as senhas
for i in range(1, 6):
    senha = input(f"Digite a senha {i}: ")
    lista_senhas.append(senha)

print("\n--- Resultado da Análise de Segurança ---")

for senha in lista_senhas:
    tamanho_ok = len(senha) >= 8
    
    # O re.search procura se existe pelo menos um padrão daquele dentro da string
    tem_maiuscula = re.search(r"[A-Z]", senha)
    tem_minuscula = re.search(r"[a-z]", senha)
    tem_numero = re.search(r"[0-9]", senha)
    tem_especial = re.search(r"[!@#$%^&*(),.?\":{}|<>]", senha)

    # Se TUDO for verdadeiro, a senha é forte
    if tamanho_ok and tem_maiuscula and tem_minuscula and tem_numero and tem_especial:
        # A senha entre aspas simples '' no print para ficar fácil ver se o usuário digitou espaços em branco
        print(f"A senha '{senha}' é FORTE. Aprovada!")
    else:
        print(f"A senha '{senha}' é FRACA. Não atende aos requisitos de segurança.")