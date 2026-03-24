import re

email = input("Digite um email: ").strip().lower()

# O padrão Regex para um e-mail básico:
# 1. ^[a-z0-9_.-]+ -> Começa com letras, números, _ . ou -
# 2. @ -> Tem que ter o @ no meio
# 3. [a-z0-9.-]+ -> Depois do @ tem domínio (ex: gmail)
# 4. \.[a-z]+$ -> Tem que terminar com um ponto e letras (ex: .com)
padrao_email = r"^[a-z0-9_.-]+@[a-z0-9.-]+\.[a-z]+$"

# A função re.match() tenta encaixar o email digitado nesse padrão
if re.match(padrao_email, email):
    print("Email válido")
    print(f"Email lido: {email}")
else:
    print("Email inválido")