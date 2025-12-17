from agno.agent import Agent
from agno.tools.yfinance import YFinanceTools
from agno.models.openai import OpenAIChat
from agno.os import AgentOS
from agno.db.sqlite import SqliteDb

import os
from dotenv import load_dotenv

load_dotenv()

# Setup your database
db = SqliteDb(id="analista_db", db_file="agno.db")

agent = Agent(
    name="analista_financeiro",
    model=OpenAIChat(id="gpt-5-nano", api_key=os.getenv("OPENAI_API_KEY"), reasoning_effort="low"),
    tools=[YFinanceTools()],
    instructions="Use tabelas para mostrar a informação final. Não inclua nenhum outro texto.",
    db=db,
)

agent_os = AgentOS(
    id="analista",
    description="Analista de investimentos",
    agents=[agent],
)

app = agent_os.get_app()

if __name__ == "__main__":
    agent_os.serve(app="12_analista:app", reload=True)

# agent.print_response("Qual é cotação atual da PETROBRAS?", stream=True)
# agent.print_response("Qual foi a empresa solicitada anteriormente e qual a cotacao foi informada?", stream=True)