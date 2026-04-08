import random

def gerar_email_fake():
    nomes = ["leonardo", "emily", "luan", "sandra"]
    nome_sorteado = random.choice(nomes)
    numero = random.randint(1000, 9999)
    return f"{nome_sorteado}{numero}@testeqa.com"

if __name__ == "__main__":
    for i in range(1, 6):
        print(gerar_email_fake())