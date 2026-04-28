import requests
import time

def mapear_golpes_hgss():
    print("Iniciando varredura na PokéAPI (Isso pode levar de 1 a 2 minutos...)")
    
    # Conjuntos (Sets) para armazenar os nomes dos golpes, garantindo que não haverá duplicatas
    level_up_moves = set()
    machine_moves = set()
    tutor_moves = set()
    egg_moves = set()

    # Na Gen 4, temos 493 Pokémon
    for poke_id in range(1, 494):
        # Um pequeno print para você saber que o programa não travou
        if poke_id % 50 == 0:
            print(f"Analisando Pokémon {poke_id}/493...")
            
        url = f"https://pokeapi.co/api/v2/pokemon/{poke_id}"
        
        try:
            resposta = requests.get(url)
            if resposta.status_code != 200:
                continue
                
            dados = resposta.json()
            
            for move_data in dados['moves']:
                nome_golpe = move_data['move']['name']
                
                for detail in move_data['version_group_details']:
                    # Filtra apenas os dados de HeartGold e SoulSilver
                    if detail['version_group']['name'] == 'heartgold-soulsilver':
                        metodo = detail['move_learn_method']['name']
                        
                        # Distribui o golpe para a caixa correta
                        if metodo == 'level-up':
                            level_up_moves.add(nome_golpe)
                        elif metodo == 'machine':
                            machine_moves.add(nome_golpe)
                        elif metodo == 'tutor':
                            tutor_moves.add(nome_golpe)
                        elif metodo == 'egg':
                            egg_moves.add(nome_golpe)
                            
        except Exception as e:
            print(f"Erro no Pokémon {poke_id}: {e}")
            
        # Pausa minúscula para não sobrecarregar o servidor da PokéAPI e tomar bloqueio
        time.sleep(0.1)

    print("\n" + "="*50)
    print("🎯 ANÁLISE CONCLUÍDA! RESULTADOS REAIS DE HGSS:")
    print("="*50)

    # A mágica acontece aqui: A subtração de conjuntos do Python pega o que tem em um mas não tem no outro!
    
    # 1. TMs/HMs que ninguém aprende por nível
    exclusivos_machine = machine_moves - level_up_moves
    print(f"\n💿 TMs/HMs NUNCA aprendidos por Level Up ({len(exclusivos_machine)} golpes):")
    print(", ".join(sorted(exclusivos_machine)))

    # 2. Move Tutors que ninguém aprende por nível
    exclusivos_tutor = tutor_moves - level_up_moves
    print(f"\n👨‍🏫 Move Tutors NUNCA aprendidos por Level Up ({len(exclusivos_tutor)} golpes):")
    print(", ".join(sorted(exclusivos_tutor)))

    # 3. Egg Moves que ninguém aprende por nível
    exclusivos_egg = egg_moves - level_up_moves
    print(f"\n🥚 Egg Moves NUNCA aprendidos por Level Up ({len(exclusivos_egg)} golpes):")
    print(", ".join(sorted(exclusivos_egg)))

if __name__ == "__main__":
    mapear_golpes_hgss()