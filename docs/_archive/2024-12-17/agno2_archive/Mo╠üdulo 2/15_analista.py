from agno.agent import Agent
from agno.tools.yfinance import YFinanceTools
from agno.models.openai import OpenAIChat
from agno.db.sqlite import SqliteDb

import os
from dotenv import load_dotenv

load_dotenv()

# Setup the SQLite database
db = SqliteDb(db_file="tmp/data.db")

agent = Agent(
    name="analista_financeiro",
    model=OpenAIChat(id="gpt-5-nano", api_key=os.getenv("OPENAI_API_KEY")),
    tools=[YFinanceTools()],
    instructions="Voce é um analista e tem diferentes clientes. Lembre-se de cada cliente, suas informações e preferências.",
    db=db,
    add_history_to_context=True,
    num_history_runs=3,
    enable_user_memories=True,
    add_memories_to_context=True,
    enable_agentic_memory=True,
)

# agent.print_response("Ola, prefiro as respostas em formato de tabelas, gosto de poucas informacoes.", session_id="petrobras_session_1", user_id="analista_petrobras")
# agent.print_response("Ola, prefiro as respostas em formato de texto, gosto de bastante detalhes.", session_id="vale_session_1", user_id="analista_vale")

agent.print_response("Qual é a cotação da petrobras?", session_id="petrobras_session_2", user_id="analista_petrobras")
agent.print_response("Qual é a cotação da vale?", session_id="vale_session_2", user_id="analista_vale")