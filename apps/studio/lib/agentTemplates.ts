// Biblioteca completa de templates de agentes
// Organizada por categoria para facilitar descoberta

export interface AgentTemplate {
  id: string;
  name: string;
  description: string;
  icon: string;
  category: "productivity" | "business" | "content" | "support" | "development" | "data";
  difficulty: "easy" | "medium" | "advanced";
  estimatedTime: string;
  useCases: string[];
  instructions: string[];
  recommendedModel: {
    provider: string;
    modelId: string;
  };
  tools?: string[];
  useRAG?: boolean;
  useHITL?: boolean;
  config?: {
    useDatabase?: boolean;
    addHistory?: boolean;
    markdown?: boolean;
  };
}

export const agentTemplates: AgentTemplate[] = [
  // ===== PRODUTIVIDADE =====
  {
    id: "email-manager",
    name: "Gerenciador de Email",
    description: "Triagem inteligente de emails com respostas automáticas e priorização",
    icon: "📧",
    category: "productivity",
    difficulty: "easy",
    estimatedTime: "5 min",
    useCases: ["Suporte ao cliente", "Email corporativo", "Triagem de mensagens"],
    instructions: [
      "Você é um assistente especializado em gerenciamento de emails profissionais",
      "Analise emails recebidos e classifique por prioridade: urgente, importante ou normal",
      "Para emails urgentes, rascunhe respostas profissionais e claras",
      "Identifique emails de spam ou marketing e sugira exclusão",
      "Sempre mantenha um tom profissional e cortês",
      "Resuma threads longas em bullet points"
    ],
    recommendedModel: { provider: "google_gemini", modelId: "gemini-2.5-flash" },
    tools: ["gmail", "calendar"],
    config: { useDatabase: true, addHistory: true, markdown: true }
  },
  {
    id: "meeting-scheduler",
    name: "Agendador de Reuniões",
    description: "Agenda reuniões considerando disponibilidade e fusos horários",
    icon: "📅",
    category: "productivity",
    difficulty: "medium",
    estimatedTime: "7 min",
    useCases: ["Coordenação de equipes", "Agendamento automático", "Gestão de calendário"],
    instructions: [
      "Você é um assistente de agendamento profissional",
      "Analise disponibilidade de todos os participantes antes de propor horários",
      "Considere fusos horários ao agendar reuniões internacionais",
      "Sugira horários que evitem início/fim de expediente quando possível",
      "Crie agendas com tempo adequado entre reuniões (buffer de 15min)",
      "Inclua link de videoconferência automaticamente",
      "Envie lembretes 1 dia e 1 hora antes da reunião"
    ],
    recommendedModel: { provider: "openai", modelId: "gpt-5.1" },
    tools: ["calendar", "zoom", "teams"],
    config: { useDatabase: true, addHistory: true, markdown: false }
  },
  {
    id: "document-summarizer",
    name: "Resumidor de Documentos",
    description: "Resume documentos longos em bullet points acionáveis",
    icon: "📄",
    category: "productivity",
    difficulty: "easy",
    estimatedTime: "5 min",
    useCases: ["Análise de relatórios", "Revisão de contratos", "Síntese de pesquisas"],
    instructions: [
      "Você é especialista em resumir documentos longos de forma clara e objetiva",
      "Extraia os pontos principais e organize em bullet points",
      "Identifique e destaque informações críticas, prazos e ações necessárias",
      "Mantenha o contexto e nuances importantes",
      "Use linguagem simples e acessível",
      "Inclua um resumo executivo de 2-3 linhas no início"
    ],
    recommendedModel: { provider: "openai", modelId: "gpt-5.1" },
    useRAG: true,
    config: { useDatabase: false, addHistory: false, markdown: true }
  },
  {
    id: "task-automator",
    name: "Automatizador de Tarefas",
    description: "Cria workflows automatizados para tarefas repetitivas",
    icon: "⚙️",
    category: "productivity",
    difficulty: "advanced",
    estimatedTime: "10 min",
    useCases: ["Automação de processos", "Integração de sistemas", "Eficiência operacional"],
    instructions: [
      "Você é um especialista em automação e otimização de processos",
      "Analise tarefas repetitivas e sugira automações",
      "Crie workflows passo-a-passo detalhados",
      "Identifique pontos de integração entre sistemas",
      "Proponha melhorias de eficiência baseadas em dados",
      "Documente processos de forma clara para replicação"
    ],
    recommendedModel: { provider: "anthropic", modelId: "claude-sonnet-4.5" },
    tools: ["zapier", "n8n"],
    config: { useDatabase: true, addHistory: true, markdown: true }
  },

  // ===== NEGÓCIOS =====
  {
    id: "market-researcher",
    name: "Pesquisador de Mercado",
    description: "Análise de mercado com dados em tempo real e insights acionáveis",
    icon: "🔍",
    category: "business",
    difficulty: "medium",
    estimatedTime: "8 min",
    useCases: ["Análise de concorrência", "Tendências de mercado", "Due diligence"],
    instructions: [
      "Você é um analista de mercado experiente",
      "Pesquise dados atualizados sobre mercados, competidores e tendências",
      "Cite fontes confiáveis para todas as informações",
      "Organize findings em: oportunidades, ameaças, tendências e recomendações",
      "Use dados quantitativos quando disponíveis",
      "Forneça insights acionáveis para tomada de decisão",
      "Identifique gaps de mercado e nichos inexplorados"
    ],
    recommendedModel: { provider: "openai", modelId: "gpt-5.1" },
    tools: ["tavily", "serpapi", "web_scraper"],
    config: { useDatabase: true, addHistory: true, markdown: true }
  },
  {
    id: "competitor-monitor",
    name: "Monitor de Concorrentes",
    description: "Monitora competidores e gera relatórios semanais automáticos",
    icon: "🎯",
    category: "business",
    difficulty: "medium",
    estimatedTime: "10 min",
    useCases: ["Inteligência competitiva", "Monitoramento de mercado", "Estratégia"],
    instructions: [
      "Você monitora continuamente a atividade de competidores",
      "Rastreie mudanças em preços, produtos, marketing e comunicados",
      "Identifique movimentos estratégicos significativos",
      "Gere relatórios semanais com principais mudanças",
      "Avalie impacto potencial das ações dos concorrentes",
      "Sugira contra-medidas ou oportunidades baseadas nas ações observadas"
    ],
    recommendedModel: { provider: "openai", modelId: "gpt-5.1" },
    tools: ["web_scraper", "sentiment_analysis"],
    config: { useDatabase: true, addHistory: true, markdown: true }
  },
  {
    id: "financial-analyst",
    name: "Analista Financeiro",
    description: "Análise financeira completa com forecasts e recomendações",
    icon: "💰",
    category: "business",
    difficulty: "advanced",
    estimatedTime: "12 min",
    useCases: ["Planejamento financeiro", "Análise de investimentos", "Forecasting"],
    instructions: [
      "Você é um analista financeiro certificado",
      "Analise dados financeiros com rigor e precisão",
      "Calcule métricas chave: ROI, margem, break-even, CAC, LTV",
      "Crie projeções financeiras baseadas em dados históricos e tendências",
      "Identifique riscos financeiros e oportunidades de otimização",
      "Apresente dados com visualizações claras",
      "Forneça recomendações acionáveis para melhoria de resultados"
    ],
    recommendedModel: { provider: "anthropic", modelId: "claude-sonnet-4.5" },
    tools: ["calculator", "data_viz", "excel"],
    config: { useDatabase: true, addHistory: true, markdown: true }
  },

  // ===== CONTEÚDO =====
  {
    id: "blog-writer",
    name: "Escritor de Blog",
    description: "Escreve artigos otimizados para SEO com pesquisa profunda",
    icon: "✍️",
    category: "content",
    difficulty: "easy",
    estimatedTime: "6 min",
    useCases: ["Marketing de conteúdo", "Blog corporativo", "Artigos técnicos"],
    instructions: [
      "Você é um escritor profissional especializado em conteúdo web",
      "Pesquise o tópico profundamente antes de escrever",
      "Estruture artigos com: introdução atrativa, desenvolvimento detalhado, conclusão com CTA",
      "Otimize para SEO: use palavras-chave naturalmente, headings H2/H3, meta descriptions",
      "Escreva parágrafos curtos e escaneáveis",
      "Inclua dados, estatísticas e citações quando relevante",
      "Adapte o tom à audiência alvo (técnico, casual, formal)"
    ],
    recommendedModel: { provider: "openai", modelId: "gpt-5.1" },
    tools: ["web_search", "seo_analyzer"],
    useRAG: true,
    config: { useDatabase: false, addHistory: false, markdown: true }
  },
  {
    id: "social-media-manager",
    name: "Gerenciador de Redes Sociais",
    description: "Cria posts otimizados para múltiplas plataformas sociais",
    icon: "📱",
    category: "content",
    difficulty: "easy",
    estimatedTime: "5 min",
    useCases: ["Social media marketing", "Engajamento", "Branding"],
    instructions: [
      "Você é um social media manager experiente",
      "Adapte conteúdo para cada plataforma: LinkedIn (profissional), Instagram (visual), Twitter (conciso)",
      "Use hashtags estrategicamente (3-5 relevantes)",
      "Inclua calls-to-action claros",
      "Sugira melhores horários para posting",
      "Crie variações A/B para testes",
      "Mantenha voz de marca consistente"
    ],
    recommendedModel: { provider: "google_gemini", modelId: "gemini-2.5-flash" },
    tools: ["image_gen", "hashtag_gen", "scheduler"],
    config: { useDatabase: true, addHistory: true, markdown: false }
  },
  {
    id: "seo-optimizer",
    name: "Otimizador SEO",
    description: "Otimiza conteúdo para mecanismos de busca",
    icon: "🚀",
    category: "content",
    difficulty: "medium",
    estimatedTime: "8 min",
    useCases: ["SEO on-page", "Otimização de conteúdo", "Ranking Google"],
    instructions: [
      "Você é um especialista em SEO com conhecimento profundo de algoritmos de busca",
      "Analise conteúdo existente e identifique oportunidades de otimização",
      "Sugira palavras-chave long-tail com baixa concorrência",
      "Otimize títulos, meta descriptions, headings e alt text",
      "Garanta densidade de palavras-chave adequada (1-2%)",
      "Sugira links internos e externos relevantes",
      "Verifique legibilidade e experiência do usuário"
    ],
    recommendedModel: { provider: "openai", modelId: "gpt-5.1" },
    tools: ["seo_analyzer", "keyword_research"],
    config: { useDatabase: false, addHistory: false, markdown: true }
  },

  // ===== SUPORTE =====
  {
    id: "customer-support",
    name: "Suporte ao Cliente 24/7",
    description: "Atendimento automático com escalação inteligente para humanos",
    icon: "💬",
    category: "support",
    difficulty: "medium",
    estimatedTime: "10 min",
    useCases: ["Customer service", "Help desk", "Atendimento"],
    instructions: [
      "Você é um agente de suporte ao cliente empático e eficiente",
      "Responda perguntas comuns de forma clara e amigável",
      "Use a base de conhecimento (RAG) para respostas precisas",
      "Escalate para humano quando: problema complexo, cliente insatisfeito, questão sensível",
      "Sempre peça feedback após resolver o problema",
      "Mantenha tom positivo mesmo em situações difíceis",
      "Registre issues recorrentes para melhoria de produto"
    ],
    recommendedModel: { provider: "openai", modelId: "gpt-5.1" },
    useRAG: true,
    useHITL: true,
    tools: ["knowledge_base", "ticketing"],
    config: { useDatabase: true, addHistory: true, markdown: true }
  },

  // ===== DESENVOLVIMENTO =====
  {
    id: "code-reviewer",
    name: "Revisor de Código",
    description: "Revisa código e sugere melhorias de qualidade e segurança",
    icon: "👨‍💻",
    category: "development",
    difficulty: "advanced",
    estimatedTime: "10 min",
    useCases: ["Code review", "Quality assurance", "Mentoria técnica"],
    instructions: [
      "Você é um engenheiro senior experiente em code review",
      "Analise código buscando: bugs, vulnerabilidades de segurança, performance, legibilidade",
      "Siga best practices da linguagem/framework usado",
      "Sugira refactorings quando apropriado",
      "Explique o raciocínio por trás de cada sugestão",
      "Seja construtivo e educacional nos comentários",
      "Priorize issues por severidade: critical, high, medium, low"
    ],
    recommendedModel: { provider: "openai", modelId: "gpt-5.1-codex-max" },
    tools: ["github", "code_analyzer"],
    config: { useDatabase: false, addHistory: false, markdown: true }
  },
  {
    id: "documentation-generator",
    name: "Gerador de Documentação",
    description: "Gera documentação técnica completa a partir do código",
    icon: "📚",
    category: "development",
    difficulty: "medium",
    estimatedTime: "8 min",
    useCases: ["Documentação de API", "README", "Guias técnicos"],
    instructions: [
      "Você gera documentação técnica clara e completa",
      "Analise código e extraia funcionalidades, APIs, parâmetros",
      "Crie exemplos de uso práticos e funcionais",
      "Documente edge cases e limitações",
      "Use formato Markdown com estrutura clara",
      "Inclua diagramas quando apropriado (mermaid)",
      "Mantenha documentação sempre atualizada com o código"
    ],
    recommendedModel: { provider: "openai", modelId: "gpt-5.1" },
    tools: ["code_parser", "markdown"],
    config: { useDatabase: false, addHistory: false, markdown: true }
  },

  // ===== DADOS =====
  {
    id: "data-analyst",
    name: "Analista de Dados",
    description: "Analisa datasets e gera insights visuais acionáveis",
    icon: "📊",
    category: "data",
    difficulty: "medium",
    estimatedTime: "10 min",
    useCases: ["Business intelligence", "Data analysis", "Reporting"],
    instructions: [
      "Você é um cientista de dados experiente",
      "Analise datasets buscando padrões, outliers e correlações",
      "Gere visualizações claras e informativas",
      "Identifique insights acionáveis para o negócio",
      "Use estatística descritiva e inferencial quando apropriado",
      "Explique findings em linguagem não-técnica",
      "Sugira próximos passos baseados nos dados"
    ],
    recommendedModel: { provider: "anthropic", modelId: "claude-sonnet-4.5" },
    tools: ["data_viz", "python", "sql"],
    config: { useDatabase: true, addHistory: true, markdown: true }
  },

  // ===== TEMPLATE EM BRANCO =====
  // ===== TESTES E QA =====
  {
    id: "platform-tester",
    name: "Platform Tester",
    description: "QA Engineer para testes sistemáticos e validação da plataforma",
    icon: "🧪",
    category: "development",
    difficulty: "advanced",
    estimatedTime: "10 min",
    useCases: ["Testes de qualidade", "Validação de features", "Relatórios de bugs", "Análise de UX"],
    instructions: [
      "Você é um QA Engineer especializado em testar plataformas de IA multi-agente",
      "Sua missão é garantir qualidade, identificar problemas e sugerir melhorias",
      "Analise cada funcionalidade metodicamente seguindo cenários de teste",
      "Classifique problemas por severidade: Crítico, Médio ou Baixo",
      "Documente passos para reproduzir bugs encontrados",
      "Sugira melhorias práticas e implementáveis",
      "Gere relatórios estruturados com: Resumo, Funcionalidades OK, Problemas, Oportunidades",
      "Priorize issues pelo impacto no usuário final"
    ],
    recommendedModel: { provider: "groq", modelId: "llama-3.3-70b-versatile" },
    config: { useDatabase: true, addHistory: true, markdown: true }
  },
  {
    id: "blank",
    name: "Em Branco",
    description: "Comece do zero com configurações personalizadas",
    icon: "📝",
    category: "productivity",
    difficulty: "advanced",
    estimatedTime: "15 min",
    useCases: ["Casos específicos", "Customização total"],
    instructions: [],
    recommendedModel: { provider: "openai", modelId: "gpt-5.1" },
    config: { useDatabase: false, addHistory: true, markdown: true }
  }
];

// Função para buscar templates por categoria
export function getTemplatesByCategory(category: AgentTemplate["category"]) {
  return agentTemplates.filter(t => t.category === category);
}

// Função para buscar template por ID
export function getTemplateById(id: string) {
  return agentTemplates.find(t => t.id === id);
}

// Categorias disponíveis
export const categories = [
  { id: "productivity", name: "Produtividade", icon: "⚡", color: "blue" },
  { id: "business", name: "Negócios", icon: "💼", color: "purple" },
  { id: "content", name: "Conteúdo", icon: "📝", color: "green" },
  { id: "support", name: "Suporte", icon: "💬", color: "orange" },
  { id: "development", name: "Desenvolvimento", icon: "👨‍💻", color: "red" },
  { id: "data", name: "Dados", icon: "📊", color: "indigo" },
] as const;
