import os

PAGAMENTO_API_KEY = os.environ.get("PAGAMENTO_API_KEY", "")

def cobrar(valor):
    return {"status": "aprovado", "valor": valor}