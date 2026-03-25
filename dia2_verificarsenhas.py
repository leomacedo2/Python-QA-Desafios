lista_senhas = []

for i in range(1, 6):
    senha = input(f"Digite a senha {i}: ")
    lista_senhas.append(senha)

for i in lista_senhas:
    if len(i) < 8:
        print(f"A senha {i} é FRACA. Minimo de 8 caracteres exigido.")
    else:
        print(f"A senha {i} é FORTE. Aprovada!")