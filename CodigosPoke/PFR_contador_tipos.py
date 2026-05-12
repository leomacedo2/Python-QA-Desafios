import requests
from collections import defaultdict

# Quantidade de Pokémon da geração 1 até 3
MAX_POKEMON = 386

# URL base da PokéAPI
BASE_URL = "https://pokeapi.co/api/v2/pokemon/"

# Dicionário para contar os tipos
contador_tipos = defaultdict(int)

print("🔎 Analisando Pokémon...\n")

for pokemon_id in range(1, MAX_POKEMON + 1):
    url = f"{BASE_URL}{pokemon_id}"

    try:
        response = requests.get(url)
        response.raise_for_status()

        dados = response.json()

        nome = dados["name"].capitalize()

        # Lista de tipos do Pokémon
        tipos = [tipo["type"]["name"] for tipo in dados["types"]]

        print(f"{pokemon_id:03d} - {nome} -> {', '.join(tipos)}")

        # Soma +1 para cada tipo
        for tipo in tipos:
            contador_tipos[tipo] += 1

    except requests.exceptions.RequestException as erro:
        print(f"Erro ao buscar Pokémon {pokemon_id}: {erro}")

print("\n" + "=" * 40)
print("📊 TOTAL DE POKÉMON POR TIPO")
print("=" * 40)

# Ordena do maior para o menor
for tipo, quantidade in sorted(
    contador_tipos.items(),
    key=lambda item: item[1],
    reverse=True
):
    print(f"{tipo.capitalize():<12} : {quantidade}")