# --- CÓDIGO DO DEV ---
def validar_acesso(usuario):
    # Se for maior de idade E estiver ativo, retorna Verdadeiro (Liberado)
    if usuario["idade"] >= 18 and usuario["status_ativo"]:
        return True
    # Para qualquer outra combinação, retorna Falso (Negado)
    else:
        return False


# --- CÓDIGO DE AUTOMAÇÃO DO QA ---
# 1. Criamos os dados de teste
usuario_caminho_feliz = {
    "nome": 'Leonardo',
    "idade": 34,
    "email": 'meuemail@gmail.com',
    "status_ativo": True
}

usuario_menor_idade = {
    "nome": 'Emily',
    "idade": 7,
    "email": 'naotememail@gmail.com',
    "status_ativo": True
}

# 2. O comando ASSERT em ação!
# Ele diz: "Python, eu AFIRMO que se eu jogar o usuario_caminho_feliz na função, o resultado tem que ser True. Se não for, quebre o programa!"
assert validar_acesso(usuario_caminho_feliz) == True

print("Teste 1 (Caminho Feliz) PASSOU COM SUCESSO! ✅")

# Afirmo que para a Emily, o acesso TEM QUE SER negado (False)
assert validar_acesso(usuario_menor_idade) == False

print("Teste 2 (Menor de idade) PASSOU COM SUCESSO! Acesso foi negado corretamente. ✅")