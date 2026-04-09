# Código para treinar teste de aleatoriedade

from dia5_gerador_dados import gerar_email_fake
import re

padrao_email = r"^[a-z]+[0-9]{4}@testeqa\.com$"

for i in range(1, 101):
    # A cada volta do laço, acionamos a função para gerar um NOVO email
    email_teste = gerar_email_fake()

    assert re.match(padrao_email, email_teste)

print("\nTodos os testes passaram! ✅")