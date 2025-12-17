"""
Agente especializado em testes e validação da plataforma Agno
"""

from typing import List, Optional, Dict, Any
from ..base_agent import BaseAgent


class PlatformTesterAgent:
    """
    Agente de teste estruturado para validação completa da plataforma.
    
    Funcionalidades:
    - Análise sistemática de funcionalidades
    - Identificação de oportunidades de melhoria
    - Detecção de erros e bugs
    - Geração de relatórios detalhados
    """
    
    INSTRUCTIONS = [
        "Você é um QA Engineer especializado em testar plataformas de IA multi-agente.",
        "Sua missão é garantir qualidade, identificar problemas e sugerir melhorias.",
        "",
        "## Metodologia de Teste",
        "1. **Análise Funcional**: Verifique se cada feature funciona conforme esperado",
        "2. **Análise de Usabilidade**: Avalie a experiência do usuário",
        "3. **Análise de Performance**: Identifique gargalos e lentidões",
        "4. **Análise de Segurança**: Verifique vulnerabilidades básicas",
        "5. **Análise de Integração**: Teste conexões entre componentes",
        "",
        "## Formato de Relatório",
        "Sempre estruture seus relatórios assim:",
        "",
        "### 📊 Resumo Executivo",
        "- Status geral: [OK/ATENÇÃO/CRÍTICO]",
        "- Features testadas: X/Y",
        "- Bugs encontrados: N (P críticos, M médios, L baixos)",
        "",
        "### ✅ Funcionalidades OK",
        "Liste o que está funcionando corretamente",
        "",
        "### ⚠️ Problemas Identificados",
        "Para cada problema:",
        "- **Severidade**: Crítico/Médio/Baixo",
        "- **Descrição**: O que acontece",
        "- **Passos para reproduzir**: Como replicar",
        "- **Impacto**: Quem/o que é afetado",
        "- **Sugestão de correção**: Como resolver",
        "",
        "### 💡 Oportunidades de Melhoria",
        "Sugestões para melhorar a plataforma",
        "",
        "### 📋 Próximos Testes Recomendados",
        "O que deve ser testado a seguir",
        "",
        "## Diretrizes",
        "- Seja específico e objetivo",
        "- Priorize problemas por impacto no usuário",
        "- Forneça evidências quando possível",
        "- Sugira soluções práticas e implementáveis"
    ]
    
    TEST_SCENARIOS = {
        "authentication": {
            "name": "Autenticação",
            "tests": [
                "Login com credenciais válidas",
                "Login com credenciais inválidas",
                "Logout e limpeza de sessão",
                "Persistência de token",
                "Expiração de token"
            ]
        },
        "agents": {
            "name": "Gestão de Agentes",
            "tests": [
                "Listar agentes disponíveis",
                "Criar novo agente (admin)",
                "Editar agente existente",
                "Excluir agente",
                "Executar agente com prompt simples",
                "Executar agente com prompt complexo"
            ]
        },
        "teams": {
            "name": "Times Multi-Agente",
            "tests": [
                "Criar time com múltiplos agentes",
                "Executar time com tarefa",
                "Verificar coordenação entre agentes"
            ]
        },
        "workflows": {
            "name": "Workflows",
            "tests": [
                "Criar workflow com passos sequenciais",
                "Executar workflow",
                "Verificar passagem de contexto entre passos"
            ]
        },
        "rag": {
            "name": "RAG (Knowledge Base)",
            "tests": [
                "Listar coleções",
                "Criar coleção",
                "Ingerir documentos",
                "Consultar base de conhecimento"
            ]
        },
        "ui_ux": {
            "name": "Interface e UX",
            "tests": [
                "Navegação entre páginas",
                "Responsividade mobile",
                "Dark mode",
                "Loading states",
                "Mensagens de erro",
                "Empty states"
            ]
        }
    }
    
    @classmethod
    def create(
        cls,
        model_provider: Optional[str] = None,
        model_id: Optional[str] = None,
        use_database: bool = True
    ):
        """
        Cria um agente de teste configurado.
        
        Args:
            model_provider: Provider do modelo (groq, openai, anthropic)
            model_id: ID específico do modelo
            use_database: Se deve persistir histórico de testes
        """
        return BaseAgent.create(
            name="Platform Tester",
            role="QA Engineer especializado em plataformas de IA multi-agente",
            instructions=cls.INSTRUCTIONS,
            model_provider=model_provider or "groq",
            model_id=model_id or "llama-3.3-70b-versatile",
            use_database=use_database,
            add_history_to_context=True,
            markdown=True,
            debug_mode=False
        )
    
    @classmethod
    def get_test_prompt(cls, scenario: str = "all") -> str:
        """
        Gera um prompt de teste estruturado.
        
        Args:
            scenario: Cenário específico ou "all" para teste completo
        """
        if scenario == "all":
            scenarios_text = "\n".join([
                f"### {data['name']}\n" + "\n".join(f"- [ ] {test}" for test in data['tests'])
                for data in cls.TEST_SCENARIOS.values()
            ])
            return f"""
# 🧪 Teste Completo da Plataforma Agno

Execute uma análise sistemática da plataforma seguindo os cenários abaixo.
Para cada item, verifique se funciona corretamente e documente problemas.

## Cenários de Teste

{scenarios_text}

## Instruções
1. Analise cada cenário metodicamente
2. Documente o status de cada teste (✅ OK, ⚠️ Problema, ❌ Falha)
3. Detalhe problemas encontrados com severidade e passos para reproduzir
4. Sugira melhorias e próximos passos

Gere um relatório completo no formato especificado nas suas instruções.
"""
        elif scenario in cls.TEST_SCENARIOS:
            data = cls.TEST_SCENARIOS[scenario]
            tests = "\n".join(f"- [ ] {test}" for test in data['tests'])
            return f"""
# 🧪 Teste: {data['name']}

Execute testes focados em {data['name']}.

## Checklist
{tests}

## Instruções
1. Teste cada item da checklist
2. Documente resultados e problemas
3. Sugira melhorias específicas para esta área

Gere um relatório detalhado.
"""
        else:
            return f"Cenário '{scenario}' não encontrado. Cenários disponíveis: {list(cls.TEST_SCENARIOS.keys())}"
    
    @classmethod
    def generate_validation_report(
        cls,
        test_results: Dict[str, Any]
    ) -> str:
        """
        Gera um relatório de validação formatado.
        
        Args:
            test_results: Dicionário com resultados dos testes
        """
        total = test_results.get("total", 0)
        passed = test_results.get("passed", 0)
        failed = test_results.get("failed", 0)
        warnings = test_results.get("warnings", 0)
        
        status = "✅ OK" if failed == 0 else "⚠️ ATENÇÃO" if failed < 3 else "❌ CRÍTICO"
        
        report = f"""
# 📊 Relatório de Validação da Plataforma

**Data:** {test_results.get("date", "N/A")}
**Status Geral:** {status}

## Métricas

| Métrica | Valor |
|:--------|:-----:|
| Total de Testes | {total} |
| Passou | {passed} |
| Falhou | {failed} |
| Avisos | {warnings} |
| Taxa de Sucesso | {(passed/total*100) if total > 0 else 0:.1f}% |

## Detalhes

"""
        
        if "issues" in test_results:
            report += "### Problemas Encontrados\n\n"
            for issue in test_results["issues"]:
                report += f"- **[{issue.get('severity', 'N/A')}]** {issue.get('description', 'N/A')}\n"
        
        if "improvements" in test_results:
            report += "\n### Melhorias Sugeridas\n\n"
            for imp in test_results["improvements"]:
                report += f"- {imp}\n"
        
        return report


# Agente singleton para uso rápido
def get_platform_tester(
    model_provider: Optional[str] = None,
    model_id: Optional[str] = None
):
    """Retorna uma instância do agente de teste."""
    return PlatformTesterAgent.create(
        model_provider=model_provider,
        model_id=model_id
    )
