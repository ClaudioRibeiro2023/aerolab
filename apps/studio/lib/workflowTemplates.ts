/**
 * Templates de Workflows pré-configurados
 */

import { WorkflowTemplate, WorkflowStep } from './workflowTypes';

export const workflowTemplates: WorkflowTemplate[] = [
  // ============== DATA & ETL ==============
  {
    id: 'data-pipeline',
    name: 'Data Pipeline',
    description: 'Pipeline ETL para extrair, transformar e carregar dados',
    category: 'Data',
    icon: 'Database',
    difficulty: 'intermediate',
    tags: ['etl', 'data', 'pipeline'],
    definition: {
      name: 'Data Pipeline',
      description: 'Pipeline de dados automatizado',
      steps: [
        { id: 'extract', type: 'action', name: 'Extract Data', config: { action_type: 'http', method: 'GET' } },
        { id: 'validate', type: 'condition', name: 'Validate Data', config: { branches: [{ condition: '${data.valid} == true', next_step: 'transform' }], default_step: 'error_handler' } },
        { id: 'transform', type: 'agent', name: 'Transform Data', config: { prompt: 'Transform the data: ${data}', output_variable: 'transformed' } },
        { id: 'load', type: 'action', name: 'Load to Destination', config: { action_type: 'http', method: 'POST' } },
      ],
      tags: ['data', 'etl']
    }
  },
  
  // ============== CONTENT ==============
  {
    id: 'content-crew',
    name: 'Content Creation Crew',
    description: 'Equipe de agentes para criar conteúdo de alta qualidade',
    category: 'Content',
    icon: 'PenTool',
    difficulty: 'advanced',
    tags: ['content', 'writing', 'multi-agent'],
    definition: {
      name: 'Content Creation Crew',
      description: 'Múltiplos agentes trabalhando juntos para criar conteúdo',
      steps: [
        { 
          id: 'crew', 
          type: 'multi_agent', 
          name: 'Content Crew', 
          config: { 
            pattern: 'sequential',
            task: '${input_topic}',
            agents: [
              { id: 'researcher', agent_id: 'researcher', role: 'Pesquisador', goal: 'Pesquisar o tópico profundamente' },
              { id: 'writer', agent_id: 'writer', role: 'Escritor', goal: 'Escrever conteúdo engajador' },
              { id: 'editor', agent_id: 'editor', role: 'Editor', goal: 'Revisar e melhorar o texto' }
            ]
          } 
        },
      ],
      tags: ['content', 'crew']
    }
  },
  {
    id: 'blog-generator',
    name: 'Blog Post Generator',
    description: 'Gera artigos de blog completos a partir de um tópico',
    category: 'Content',
    icon: 'FileText',
    difficulty: 'beginner',
    tags: ['blog', 'writing', 'seo'],
    definition: {
      name: 'Blog Post Generator',
      steps: [
        { id: 'research', type: 'agent', name: 'Research Topic', config: { prompt: 'Research the topic: ${topic}. Find key facts and statistics.', output_variable: 'research' } },
        { id: 'outline', type: 'agent', name: 'Create Outline', config: { prompt: 'Create a blog outline based on: ${research}', output_variable: 'outline' } },
        { id: 'write', type: 'agent', name: 'Write Content', config: { prompt: 'Write the blog post following: ${outline}', output_variable: 'content' } },
        { id: 'seo', type: 'agent', name: 'SEO Optimization', config: { prompt: 'Add SEO elements to: ${content}', output_variable: 'final' } },
      ],
      tags: ['blog', 'seo']
    }
  },
  
  // ============== CUSTOMER SERVICE ==============
  {
    id: 'support-router',
    name: 'Support Ticket Router',
    description: 'Classifica e roteia tickets de suporte automaticamente',
    category: 'Customer Service',
    icon: 'Headphones',
    difficulty: 'intermediate',
    tags: ['support', 'routing', 'classification'],
    definition: {
      name: 'Support Ticket Router',
      steps: [
        { id: 'classify', type: 'agent', name: 'Classify Ticket', config: { prompt: 'Classify this ticket into: billing, technical, sales, other.\nTicket: ${ticket}', output_variable: 'category' } },
        { id: 'route', type: 'condition', name: 'Route by Category', config: { switch_variable: 'category', cases: { 'billing': 'billing_handler', 'technical': 'tech_handler', 'sales': 'sales_handler' }, default_step: 'general_handler' } },
        { id: 'billing_handler', type: 'agent', name: 'Billing Handler', config: { prompt: 'Handle billing issue: ${ticket}' } },
        { id: 'tech_handler', type: 'agent', name: 'Technical Handler', config: { prompt: 'Handle technical issue: ${ticket}' } },
        { id: 'sales_handler', type: 'agent', name: 'Sales Handler', config: { prompt: 'Handle sales inquiry: ${ticket}' } },
        { id: 'general_handler', type: 'agent', name: 'General Handler', config: { prompt: 'Handle general inquiry: ${ticket}' } },
      ],
      tags: ['support', 'routing']
    }
  },
  {
    id: 'sentiment-response',
    name: 'Sentiment-Based Response',
    description: 'Analisa sentimento e gera resposta apropriada',
    category: 'Customer Service',
    icon: 'Heart',
    difficulty: 'beginner',
    tags: ['sentiment', 'response', 'customer'],
    definition: {
      name: 'Sentiment Response',
      steps: [
        { id: 'analyze', type: 'agent', name: 'Analyze Sentiment', config: { prompt: 'Analyze the sentiment of: ${message}\nReturn: positive, negative, or neutral', output_variable: 'sentiment' } },
        { id: 'route', type: 'condition', name: 'Route by Sentiment', config: { switch_variable: 'sentiment', cases: { 'positive': 'positive_response', 'negative': 'negative_response' }, default_step: 'neutral_response' } },
        { id: 'positive_response', type: 'agent', name: 'Positive Response', config: { prompt: 'Generate enthusiastic response to: ${message}' } },
        { id: 'negative_response', type: 'agent', name: 'Negative Response', config: { prompt: 'Generate empathetic response to: ${message}' } },
        { id: 'neutral_response', type: 'agent', name: 'Neutral Response', config: { prompt: 'Generate helpful response to: ${message}' } },
      ],
      tags: ['sentiment']
    }
  },
  
  // ============== AUTOMATION ==============
  {
    id: 'approval-flow',
    name: 'Approval Workflow',
    description: 'Fluxo de aprovação com múltiplos níveis',
    category: 'Automation',
    icon: 'CheckCircle',
    difficulty: 'intermediate',
    tags: ['approval', 'workflow', 'automation'],
    definition: {
      name: 'Approval Flow',
      steps: [
        { id: 'validate', type: 'agent', name: 'Validate Request', config: { prompt: 'Validate this request: ${request}', output_variable: 'validation' } },
        { id: 'check_valid', type: 'condition', name: 'Is Valid?', config: { branches: [{ condition: '${validation.valid} == true', next_step: 'check_amount' }], default_step: 'reject' } },
        { id: 'check_amount', type: 'condition', name: 'Check Amount', config: { branches: [{ condition: '${request.amount} > 10000', next_step: 'manager_approval' }], default_step: 'auto_approve' } },
        { id: 'manager_approval', type: 'wait', name: 'Await Manager', config: { wait_type: 'approval', timeout_hours: 48 } },
        { id: 'auto_approve', type: 'action', name: 'Auto Approve', config: { action_type: 'webhook' } },
        { id: 'reject', type: 'action', name: 'Reject', config: { action_type: 'webhook' } },
      ],
      tags: ['approval']
    }
  },
  {
    id: 'batch-processor',
    name: 'Batch Processor',
    description: 'Processa uma lista de items em lote',
    category: 'Automation',
    icon: 'Layers',
    difficulty: 'intermediate',
    tags: ['batch', 'loop', 'processing'],
    definition: {
      name: 'Batch Processor',
      steps: [
        { id: 'load', type: 'action', name: 'Load Items', config: { action_type: 'http' } },
        { id: 'process', type: 'loop', name: 'Process Each', config: { loop_type: 'for_each', items_variable: 'items', item_variable: 'item', step_config: { type: 'agent', prompt: 'Process: ${item}' } } },
        { id: 'aggregate', type: 'agent', name: 'Aggregate Results', config: { prompt: 'Summarize results: ${results}' } },
        { id: 'notify', type: 'action', name: 'Send Notification', config: { action_type: 'webhook' } },
      ],
      tags: ['batch', 'loop']
    }
  },
  
  // ============== ANALYSIS ==============
  {
    id: 'parallel-analysis',
    name: 'Parallel Analysis',
    description: 'Executa múltiplas análises em paralelo',
    category: 'Analysis',
    icon: 'BarChart2',
    difficulty: 'advanced',
    tags: ['parallel', 'analysis', 'multi'],
    definition: {
      name: 'Parallel Analysis',
      steps: [
        { 
          id: 'analyze', 
          type: 'parallel', 
          name: 'Multi Analysis', 
          config: { 
            join_strategy: 'all',
            parallel_branches: [
              { id: 'sentiment', step_type: 'agent', config: { prompt: 'Analyze sentiment: ${input}' } },
              { id: 'entities', step_type: 'agent', config: { prompt: 'Extract entities: ${input}' } },
              { id: 'summary', step_type: 'agent', config: { prompt: 'Summarize: ${input}' } },
              { id: 'keywords', step_type: 'agent', config: { prompt: 'Extract keywords: ${input}' } },
            ]
          } 
        },
        { id: 'combine', type: 'agent', name: 'Combine Results', config: { prompt: 'Combine analysis results: ${analyze}' } },
      ],
      tags: ['parallel', 'analysis']
    }
  },
  {
    id: 'expert-debate',
    name: 'Expert Debate',
    description: 'Múltiplos especialistas debatem até consenso',
    category: 'Analysis',
    icon: 'MessageCircle',
    difficulty: 'advanced',
    tags: ['debate', 'consensus', 'multi-agent'],
    definition: {
      name: 'Expert Debate',
      steps: [
        { 
          id: 'debate', 
          type: 'multi_agent', 
          name: 'Expert Debate', 
          config: { 
            pattern: 'debate',
            task: '${question}',
            max_rounds: 5,
            agents: [
              { id: 'optimist', agent_id: 'expert', role: 'Optimist', backstory: 'You always see the positive side' },
              { id: 'skeptic', agent_id: 'expert', role: 'Skeptic', backstory: 'You question everything critically' },
              { id: 'pragmatist', agent_id: 'expert', role: 'Pragmatist', backstory: 'You focus on practical solutions' },
            ]
          } 
        },
      ],
      tags: ['debate', 'multi-agent']
    }
  },
  
  // ============== INTEGRATIONS ==============
  {
    id: 'webhook-handler',
    name: 'Webhook Handler',
    description: 'Processa webhooks externos e executa ações',
    category: 'Integration',
    icon: 'Webhook',
    difficulty: 'beginner',
    tags: ['webhook', 'api', 'integration'],
    definition: {
      name: 'Webhook Handler',
      steps: [
        { id: 'parse', type: 'agent', name: 'Parse Payload', config: { prompt: 'Parse and validate webhook payload: ${payload}', output_variable: 'parsed' } },
        { id: 'process', type: 'agent', name: 'Process Event', config: { prompt: 'Process the event: ${parsed}', output_variable: 'result' } },
        { id: 'respond', type: 'action', name: 'Send Response', config: { action_type: 'webhook' } },
      ],
      tags: ['webhook']
    }
  },
  {
    id: 'scheduled-report',
    name: 'Scheduled Report',
    description: 'Gera e envia relatórios automaticamente',
    category: 'Integration',
    icon: 'Calendar',
    difficulty: 'intermediate',
    tags: ['schedule', 'report', 'email'],
    definition: {
      name: 'Scheduled Report',
      steps: [
        { id: 'fetch', type: 'action', name: 'Fetch Data', config: { action_type: 'http' } },
        { id: 'analyze', type: 'agent', name: 'Analyze Data', config: { prompt: 'Analyze this data and identify trends: ${data}' } },
        { id: 'generate', type: 'agent', name: 'Generate Report', config: { prompt: 'Generate a report from: ${analyze}' } },
        { id: 'send', type: 'action', name: 'Send Email', config: { action_type: 'email' } },
      ],
      tags: ['report', 'schedule']
    }
  },
];

// Categorias disponíveis
export const workflowCategories = [
  { id: 'all', name: 'All Templates', icon: 'Grid' },
  { id: 'Data', name: 'Data & ETL', icon: 'Database' },
  { id: 'Content', name: 'Content Creation', icon: 'PenTool' },
  { id: 'Customer Service', name: 'Customer Service', icon: 'Headphones' },
  { id: 'Automation', name: 'Automation', icon: 'Zap' },
  { id: 'Analysis', name: 'Analysis', icon: 'BarChart2' },
  { id: 'Integration', name: 'Integrations', icon: 'Link' },
];

// Busca templates
export function searchTemplates(query: string, category?: string): WorkflowTemplate[] {
  let results = workflowTemplates;
  
  if (category && category !== 'all') {
    results = results.filter(t => t.category === category);
  }
  
  if (query) {
    const lowerQuery = query.toLowerCase();
    results = results.filter(t => 
      t.name.toLowerCase().includes(lowerQuery) ||
      t.description.toLowerCase().includes(lowerQuery) ||
      t.tags.some(tag => tag.includes(lowerQuery))
    );
  }
  
  return results;
}

// Obtém template por ID
export function getTemplateById(id: string): WorkflowTemplate | undefined {
  return workflowTemplates.find(t => t.id === id);
}
