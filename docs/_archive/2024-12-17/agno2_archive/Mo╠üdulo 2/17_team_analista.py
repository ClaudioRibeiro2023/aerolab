from agno.agent import Agent
from agno.tools.yfinance import YFinanceTools
from agno.models.openai import OpenAIChat
from agno.db.sqlite import SqliteDb

from agno.vectordb.chroma import ChromaDb
from agno.knowledge.knowledge import Knowledge
from agno.knowledge.reader.pdf_reader import PDFReader
from agno.knowledge.chunking.semantic import SemanticChunking
from agno.knowledge.embedder.openai import OpenAIEmbedder

from agno.team.team import Team
from agno.tools.duckduckgo import DuckDuckGoTools

import os
from dotenv import load_dotenv

load_dotenv()

# STORAGE ===============================================
# Setup the SQLite database
db = SqliteDb(db_file="tmp/data.db")


# RAG ==================================================
# Initialize ChromaDB
vector_db = ChromaDb(
    collection="empresas_relatorios",
    path="tmp/chromadb",
    embedder=OpenAIEmbedder(id="text-embedding-3-small", api_key=os.getenv("OPENAI_API_KEY")),
    persistent_client=True
)

# Create knowledge base
knowledge = Knowledge(
    vector_db=vector_db,
)

knowledge.add_content(
    path="files/PETR/",
    reader=PDFReader(
        chunck_strategy=SemanticChunking()
    ),
    metadata={
        "company": "Petrobras",
        "sector": "Petróleo e Gás",
        "country": "Brazil",
    },
    skip_if_exists=True
)

knowledge.add_content(
    path="files/VALE/",
    reader=PDFReader(
        chunck_strategy=SemanticChunking()
    ),
    metadata={
        "company": "Vale",
        "sector": "Mineração",
        "country": "Brazil",
    },
    skip_if_exists=True
)


# AGENT ================================================
analista_noticias_agent = Agent(
    name="analista_noticias",
    model=OpenAIChat(id="gpt-5-nano", api_key=os.getenv("OPENAI_API_KEY")),
    role="Voce é um pesquisador de noticias.",
    instructions=[
        "Use suas tools de busca para encontrar informações na web sobre empresas listadas na B3."
    ],
    tools=[DuckDuckGoTools(enable_search=False, enable_news=True)],
    markdown=True,
)

analista_cotacoes_agent = Agent(
    name="analista_cotacoes",
    model=OpenAIChat(id="gpt-5-nano", api_key=os.getenv("OPENAI_API_KEY")),
    tools=[YFinanceTools()],
    instructions="Voce é um analista de cotacoes de empresas listadas na B3.",
    markdown=True,
)

analista_relatorios_agent = Agent(
    name="analista_relatorios",
    model=OpenAIChat(id="gpt-5-nano", api_key=os.getenv("OPENAI_API_KEY")),
    instructions="Voce é um analista de relatorios de empresas listadas na B3.",
    knowledge=knowledge,
    add_knowledge_to_context=True,
    markdown=True,
)

analista_team = Team(
    name="Team Analista",
    model=OpenAIChat(id="gpt-5-nano", api_key=os.getenv("OPENAI_API_KEY")),
    members=[analista_noticias_agent, analista_cotacoes_agent, analista_relatorios_agent],
    instructions=[
        "Voce deve entender as informacoes solicitadas pelo usuario e fornecer uma resposta adequada.",
        "Para obter informacoes sobre balanco e DRE, utilize o analista_relatorios.",
        "Para obter informacoes sobre cotacoes, utilize o analista_cotacoes.",
        "Para obter informacoes sobre noticias, utilize o analista_noticias.",
    ],
    db=db,
    add_history_to_context=True,
    num_history_runs=3,
    show_members_responses=True,
    get_member_information_tool=True,
    add_datetime_to_context=True,
    markdown=True,
)

# agent.print_response("Ola, prefiro as respostas em formato de tabelas, gosto de poucas informacoes.", session_id="petrobras_session_1", user_id="analista_petrobras")
# agent.print_response("Ola, prefiro as respostas em formato de texto, gosto de bastante detalhes.", session_id="vale_session_1", user_id="analista_vale")

# agent.print_response("Qual é a cotação da petrobras?", session_id="petrobras_session_2", user_id="analista_petrobras")
# agent.print_response("Qual é a cotação da vale?", session_id="vale_session_2", user_id="analista_vale")

# analista_team.print_response("Ola, qual foi o lucro liquido da petrobras em 2T25 segundo o relatorio publicado?", session_id="petrobras_session_10", user_id="analista_petrobras")
# analista_team.print_response("e quais sao as principais noticias sobre petrobras hoje?", session_id="petrobras_session_6", user_id="analista_petrobras")
analista_team.print_response("Qual a cotação da petrobras e quais noticias podem ter movimentado a cotação nos ultimos dias?", session_id="petrobras_session_10", user_id="analista_petrobras")