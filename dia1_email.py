email = input("Digite um email: ")

# Limpa os espaços e já converte tudo para minúsculo na mesma linha!
email = email.strip().lower()

if "@" in email and "." in email:
    print("Email válido")
    print(f"Email lido: {email}")
else:    
    print("Email inválido")
