usuario_teste = {
    "nome": 'Leonardo',
    "idade": 34,
    "email": 'meuemail@gmail.com',
    "status_ativo": True
}

if usuario_teste["idade"]>= 18 and usuario_teste["status_ativo"]:
    print(f"Acesso Liberado para {usuario_teste['nome']}")
elif usuario_teste["idade"]<18 and usuario_teste["status_ativo"] :
    print("Acesso Negado. Usuario menor de idade")
elif usuario_teste["idade"]>=18 and  not usuario_teste["status_ativo"]:
    print("Acesso Negado. Conta Inativa")
else:
    print("Acesso Negado. Não atende nenhum dos dois requisitos.")