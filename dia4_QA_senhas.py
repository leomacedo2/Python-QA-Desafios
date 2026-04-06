# Importando a função do arquivo do Dev (dia4_funcoes.py)
from dia4_funcoes import validar_forca_senha

print("Iniciando Bateria de Testes Automatizados...\n")

# 1. Caminho Feliz (A senha perfeita - tem que dar True)
assert validar_forca_senha("Forte@2026") == True

# 2. Testando a regra do Tamanho (Menos de 8 chars - tem que dar False)
assert validar_forca_senha("F@2026a") == False

# 3. Testando a regra da Maiúscula (Tudo minúsculo - tem que dar False)
assert validar_forca_senha("forte@2026") == False

# 4. Testando a regra da Minúscula (Tudo maiúsculo - tem que dar False)
assert validar_forca_senha("FORTE@2026") == False

# 5. Testando a regra de Números (Sem numeros - tem que dar False)
assert validar_forca_senha("ForteForte@@") == False

# 6. Testando a regra de Caractere especial (Sem Caractere - tem que dar False)
assert validar_forca_senha("Forte2026") == False

print("\nTodos os testes passaram! A Regra de Negócio está correta! ✅")