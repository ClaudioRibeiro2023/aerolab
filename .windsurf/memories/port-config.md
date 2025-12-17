# Configuração de Portas - AeroLab

## Regra Principal
**A aplicação frontend SEMPRE deve rodar na porta 9000.**

## Portas Padrão

| Serviço | Porta | URL |
|---------|-------|-----|
| **Frontend (Studio)** | 9000 | http://localhost:9000 |
| **Backend (API)** | 8000 | http://localhost:8000 |

## Configuração

O script `dev` em `apps/studio/package.json` está configurado para:
```json
"dev": "next dev -p 9000"
```

## Importante
- Todas as entregas e testes devem ser feitos na porta 9000
- O browser preview deve apontar para http://localhost:9000
- Esta configuração é permanente para o projeto AeroLab
