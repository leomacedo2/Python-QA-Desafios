import requests
import time

def mapear_golpes_frlg():
    print("Iniciando varredura na PokéAPI para FireRed/LeafGreen...")
    print("(Isso pode levar de 1 a 2 minutos)")
    
    level_up_moves = set()
    machine_moves = set()
    tutor_moves = set()
    egg_moves = set()

    # Na Gen 3 (FireRed/LeafGreen), temos 386 Pokémon
    for poke_id in range(1, 387):
        if poke_id % 50 == 0:
            print(f"Analisando Pokémon {poke_id}/386...")
            
        url = f"https://pokeapi.co/api/v2/pokemon/{poke_id}"
        
        try:
            resposta = requests.get(url)
            if resposta.status_code != 200:
                continue
                
            dados = resposta.json()
            
            for move_data in dados['moves']:
                nome_golpe = move_data['move']['name']
                
                for detail in move_data['version_group_details']:
                    # Filtra apenas os dados de FireRed e LeafGreen
                    if detail['version_group']['name'] == 'firered-leafgreen':
                        metodo = detail['move_learn_method']['name']
                        
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
            
        # Pausa para não sobrecarregar a API
        time.sleep(0.1)

    print("\n" + "="*50)
    print("🎯 ANÁLISE CONCLUÍDA! RESULTADOS REAIS DE FIRERED/LEAFGREEN:")
    print("="*50)

    # Subtração de conjuntos
    exclusivos_machine = machine_moves - level_up_moves
    print(f"\n💿 TMs/HMs NUNCA aprendidos por Level Up ({len(exclusivos_machine)} golpes):")
    print(", ".join(sorted(exclusivos_machine)))

    exclusivos_tutor = tutor_moves - level_up_moves
    print(f"\n👨‍🏫 Move Tutors NUNCA aprendidos por Level Up ({len(exclusivos_tutor)} golpes):")
    print(", ".join(sorted(exclusivos_tutor)))

    exclusivos_egg = egg_moves - level_up_moves
    print(f"\n🥚 Egg Moves NUNCA aprendidos por Level Up ({len(exclusivos_egg)} golpes):")
    print(", ".join(sorted(exclusivos_egg)))

if __name__ == "__main__":
    mapear_golpes_frlg()