import re

def validar_forca_senha(senha):
    # Validações básicas
    tamanho_ok = len(senha) >= 8
    tem_maiuscula = re.search(r"[A-Z]", senha)
    tem_minuscula = re.search(r"[a-z]", senha)
    tem_numero = re.search(r"[0-9]", senha)
    tem_especial = re.search(r"[!@#$%^&*(),.?\":{}|<>]", senha)
    
    # Validações adicionais
    sem_espacos = " " not in senha
    
    # Evitar repetição excessiva (3+ caracteres iguais seguidos)
    sem_repeticoes = not re.search(r"(.)\1{2,}", senha)
    
    # Evitar sequências numéricas (12345, 23456, etc)
    sem_seq_numeros = not any(
        str(i) + str(i+1) + str(i+2) + str(i+3) in senha
        for i in range(7)
    )
    
    # Evitar sequências alfabéticas (abcde, bcdef, etc)
    alfabeto = "abcdefghijklmnopqrstuvwxyz"
    sem_seq_letras = not any(
        alfabeto[i:i+4] in senha.lower()
        for i in range(len(alfabeto) - 3)
    )
    
    # Evitar padrões muito comuns (admin, password, 123456)
    padroes_bloqueados = ["admin", "password", "123456", "qwerty", "abc123"]
    sem_padroes = not any(padrao in senha.lower() for padrao in padroes_bloqueados)
    
    if (tamanho_ok and tem_maiuscula and tem_minuscula and tem_numero and 
        tem_especial and sem_espacos and sem_repeticoes and sem_seq_numeros and 
        sem_seq_letras and sem_padroes):
        return True
    else:
        return False


# Uma tecnica para que esses prints só rodem se for este arquivo a ser executado.
if __name__ == "__main__":
    print(validar_forca_senha("senha123"))
    print(validar_forca_senha("Forte@2026"))