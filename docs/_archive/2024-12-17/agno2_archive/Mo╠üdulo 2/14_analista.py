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
    instructions="Use tabelas para mostrar a informação final. Não inclua nenhum outro texto.",
    db=db,
    add_history_to_context=True,
    num_history_runs=3
)

agent.print_response("Qual é a cotação da petrobras?", session_id="petrobras_session", user_id="analista_petrobras")
agent.print_response("Qual é a cotação da vale?", session_id="vale_session", user_id="analista_vale")
agent.print_response("Quais empresas ja consultamos a cotação?", session_id="petrobras_session", user_id="analista_empresas")