from dia5_gerador_dados import gerar_email_fake
import re

# A função precisa começar com "test_"
def test_gerar_email_aleatorio_valido():
    padrao_email = r"^[a-z]+[0-9]{4}@testeqa\.com$"
    
    # Podemos manter o laço for dentro do teste para garantir a aleatoriedade
    for i in range(1, 101):
        email_teste = gerar_email_fake()
        assert re.match(padrao_email, email_teste)