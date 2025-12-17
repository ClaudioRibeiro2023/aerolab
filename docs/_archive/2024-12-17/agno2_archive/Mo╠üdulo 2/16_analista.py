from agno.agent import Agent
from agno.tools.yfinance import YFinanceTools
from agno.models.openai import OpenAIChat
from agno.db.sqlite import SqliteDb

from agno.vectordb.chroma import ChromaDb
from agno.knowledge.knowledge import Knowledge
from agno.knowledge.reader.pdf_reader import PDFReader
from agno.knowledge.chunking.semantic import SemanticChunking
from agno.knowledge.embedder.openai import OpenAIEmbedder

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
    knowledge=knowledge,
    add_knowledge_to_context=True
)

# agent.print_response("Ola, prefiro as respostas em formato de tabelas, gosto de poucas informacoes.", session_id="petrobras_session_1", user_id="analista_petrobras")
# agent.print_response("Ola, prefiro as respostas em formato de texto, gosto de bastante detalhes.", session_id="vale_session_1", user_id="analista_vale")

# agent.print_response("Qual é a cotação da petrobras?", session_id="petrobras_session_2", user_id="analista_petrobras")
# agent.print_response("Qual é a cotação da vale?", session_id="vale_session_2", user_id="analista_vale")

agent.print_response("Ola, qual foi o lucro liquido da petrobras em 2T25?", session_id="petrobras_session_4", user_id="analista_petrobras")
agent.print_response("Ola, o que foi comentado sobre o CAPEX da vale no 2T25?", session_id="vale_session_4", user_id="analista_vale")
