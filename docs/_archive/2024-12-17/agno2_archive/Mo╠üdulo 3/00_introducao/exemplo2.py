# ----------------------------------------------------------------------------
# Conta Corrente Bancária - FastAPI
# Gerenciar saques e depósitos de clientes
# ----------------------------------------------------------------------------


# IMPORTS ===========================================================
from fastapi import FastAPI
import uvicorn
from pydantic import BaseModel, Field

# inicializa o fastapi
app = FastAPI(title="Conta Bancaria - Conta Correte")

# Adicionar clientes (simulacao de banco de dados)
db_clientes = {
    "Joao": 0,
    "Maria": 0,
    "Pedro": 0,
}

# criar uma classe para as movimentações (saques e depósitos) OBS: usar pydantic (para nao aconter erros)
class Movimentacao(BaseModel):
    cliente: str = Field(..., description="Nome do cliente")
    valor: float = Field(..., gt=0, description="Valor da movimentacao")

# Criar um endpoint HOME (raiz)
@app.get("/")
def read_root():
    return {"message": "Conta Bancaria - Conta Correte"}

# Criar um endpoint para consultar o saldo
@app.post("/saldo")
def saldo(cliente: str):
    return {"message": f"Saldo do cliente {cliente} é {db_clientes[cliente]}"}

# Criar um endpoint para realizar saques
@app.post("/saque")
def saque(movimentacao: Movimentacao):
    db_clientes[movimentacao.cliente] -= movimentacao.valor
    return {"message": {"cliente": movimentacao.cliente, "valor_movimentacao": -movimentacao.valor, "saldo": db_clientes[movimentacao.cliente]}}

# Criar um endpoint para realizar depósitos
@app.post("/deposito")
def deposito(movimentacao: Movimentacao):
    db_clientes[movimentacao.cliente] += movimentacao.valor
    return {"message": {"cliente": movimentacao.cliente, "valor_movimentacao": movimentacao.valor, "saldo": db_clientes[movimentacao.cliente]}}


# RUN ===========================================================
if __name__ == "__main__":
    uvicorn.run("exemplo2:app", host="0.0.0.0", port=8000, reload=True)