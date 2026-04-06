import re

def validar_forca_senha(senha):
    tamanho_ok = len(senha) >= 8
    tem_maiuscula = re.search(r"[A-Z]", senha)
    tem_minuscula = re.search(r"[a-z]", senha)
    tem_numero = re.search(r"[0-9]", senha)
    tem_especial = re.search(r"[!@#$%^&*(),.?\":{}|<>]", senha)
    
    if tamanho_ok and tem_maiuscula and tem_minuscula and tem_numero and tem_especial:
        return True
    else:
        return False


# Uma tecnica para que esses prints só rodem se for este arquivo a ser executado.
if __name__ == "__main__":
    print(validar_forca_senha("senha123"))
    print(validar_forca_senha("Forte@2026"))