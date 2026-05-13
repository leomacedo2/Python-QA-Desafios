import requests
from collections import defaultdict

BASE_URL = "https://pokeapi.co/api/v2/pokemon/"

# Tipos válidos da Gen 3
TIPOS_GEN3 = {
    "normal",
    "fire",
    "water",
    "electric",
    "grass",
    "ice",
    "fighting",
    "poison",
    "ground",
    "flying",
    "psychic",
    "bug",
    "rock",
    "ghost",
    "dragon",
    "dark",
    "steel"
}

# Correções manuais dos Pokémon afetados pelo tipo Fairy
CORRECOES_GEN3 = {
    35: ["normal"],             # Clefairy
    36: ["normal"],             # Clefable
    39: ["normal"],             # Jigglypuff
    40: ["normal"],             # Wigglytuff
    173: ["normal"],            # Cleffa
    174: ["normal"],            # Igglybuff
    175: ["normal"],            # Togepi
    176: ["normal", "flying"],  # Togetic
    209: ["normal"],            # Snubbull
    210: ["normal"],            # Granbull
    280: ["psychic"],           # Ralts
    281: ["psychic"],           # Kirlia
    282: ["psychic"],           # Gardevoir
    298: ["normal"],            # Azurill
}

contador_tipos = defaultdict(int)

print("🔎 Analisando Pokémon da Gen 3...\n")

for pokemon_id in range(1, 387):

    try:
        response = requests.get(f"{BASE_URL}{pokemon_id}")
        response.raise_for_status()

        dados = response.json()

        nome = dados["name"].capitalize()

        # Se tiver correção manual
        if pokemon_id in CORRECOES_GEN3:
            tipos = CORRECOES_GEN3[pokemon_id]

        else:
            tipos = [
                tipo["type"]["name"]
                for tipo in dados["types"]
                if tipo["type"]["name"] in TIPOS_GEN3
            ]

        print(f"{pokemon_id:03d} - {nome} -> {', '.join(tipos)}")

        for tipo in tipos:
            contador_tipos[tipo] += 1

    except requests.exceptions.RequestException as erro:
        print(f"Erro no Pokémon {pokemon_id}: {erro}")

print("\n" + "=" * 40)
print("📊 TOTAL DE POKÉMON POR TIPO (GEN 3)")
print("=" * 40)

for tipo, quantidade in sorted(
    contador_tipos.items(),
    key=lambda item: item[1],
    reverse=True
):
    print(f"{tipo.capitalize():<12} : {quantidade}")