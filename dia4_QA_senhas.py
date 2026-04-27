# Importando a função do arquivo do Dev (dia4_funcoes.py)
from dia4_funcoes import validar_forca_senha

print("Iniciando Bateria de Testes Automatizados...\n")

# --- TESTES ORIGINAIS (Regras Básicas) ---
print("=== TESTANDO REGRAS BÁSICAS ===")

# 1. Caminho Feliz (A senha perfeita - tem que dar True)
assert validar_forca_senha("Forte@2026") == True
print("✅ Teste 1: Caminho feliz - Senha válida")

# 2. Testando a regra do Tamanho (Menos de 8 chars - tem que dar False)
assert validar_forca_senha("F@2026a") == False
print("✅ Teste 2: Tamanho insuficiente")

# 3. Testando a regra da Maiúscula (Tudo minúsculo - tem que dar False)
assert validar_forca_senha("forte@2026") == False
print("✅ Teste 3: Sem letras maiúsculas")

# 4. Testando a regra da Minúscula (Tudo maiúsculo - tem que dar False)
assert validar_forca_senha("FORTE@2026") == False
print("✅ Teste 4: Sem letras minúsculas")

# 5. Testando a regra de Números (Sem numeros - tem que dar False)
assert validar_forca_senha("ForteForte@@") == False
print("✅ Teste 5: Sem números")

# 6. Testando a regra de Caractere especial (Sem Caractere - tem que dar False)
assert validar_forca_senha("Forte2026") == False
print("✅ Teste 6: Sem caracteres especiais")

# --- NOVOS TESTES (Validações Adicionais) ---
print("\n=== TESTANDO VALIDAÇÕES ADICIONAIS ===")

# 7. Testando espaços em branco (com espaço - tem que dar False)
assert validar_forca_senha("Forte @2026") == False
print("✅ Teste 7: Rejeita espaços em branco")

# 8. Testando espaços no final
assert validar_forca_senha("Forte@2026 ") == False
print("✅ Teste 8: Rejeita espaço no final")

# 9. Testando repetição de caracteres (aaa - tem que dar False)
assert validar_forca_senha("Forteee@2026") == False
print("✅ Teste 9: Rejeita 3+ caracteres repetidos")

# 10. Testando repetição de caracteres extrema (aaaa)
assert validar_forca_senha("Forte@2222") == False
print("✅ Teste 10: Rejeita 4+ caracteres repetidos")

# 11. Testando sequência numérica (1234 - tem que dar False)
assert validar_forca_senha("Forte@1234") == False
print("✅ Teste 11: Rejeita sequência numérica (1234)")

# 12. Testando sequência numérica 5678
assert validar_forca_senha("Rua@Numero5678") == False
print("✅ Teste 12: Rejeita sequência numérica (5678)")

# 13. Testando sequência alfabética (abcd - tem que dar False)
assert validar_forca_senha("Abcde@2026") == False
print("✅ Teste 13: Rejeita sequência alfabética (abcde)")

# 14. Testando sequência alfabética inversa
assert validar_forca_senha("Xyzwv@2026") == False
print("✅ Teste 14: Rejeita sequência alfabética (xyzw)")

# 15. Testando palavra bloqueada "admin"
assert validar_forca_senha("Admin@2026") == False
print("✅ Teste 15: Rejeita padrão 'admin'")

# 16. Testando palavra bloqueada "password"
assert validar_forca_senha("Password@123") == False
print("✅ Teste 16: Rejeita padrão 'password'")

# 17. Testando padrão "123456"
assert validar_forca_senha("Teste@123456") == False
print("✅ Teste 17: Rejeita padrão '123456'")

# 18. Testando padrão "qwerty"
assert validar_forca_senha("Qwerty@2026") == False
print("✅ Teste 18: Rejeita padrão 'qwerty'")

# 19. Testando padrão "abc123"
assert validar_forca_senha("Abc123@pass") == False
print("✅ Teste 19: Rejeita padrão 'abc123'")

# 20. Testando senha válida com caracteres especiais variados
assert validar_forca_senha("Segur@nça2026") == True
print("✅ Teste 20: Aceita senhas válidas com caracteres especiais")

# 21. Testando outra senha válida
assert validar_forca_senha("MyP@ssw0rd") == True
print("✅ Teste 21: Aceita outra senha válida")

# 22. Testando comprimento no limite mínimo (8 caracteres)
assert validar_forca_senha("Abc@1234") == True
print("✅ Teste 22: Aceita 8 caracteres (mínimo)")

# 23. Testando comprimento longo
assert validar_forca_senha("UmaSenhaM@itoForte123456789") == True
print("✅ Teste 23: Aceita senhas longas")

print("\n" + "="*50)
print("🎉 Todos os testes passaram!")
print("✅ A Regra de Negócio está robusta e segura!")
print("="*50)