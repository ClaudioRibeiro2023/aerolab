#!/usr/bin/env node
/* eslint-disable @typescript-eslint/no-var-requires, no-console */
/**
 * Script para criar estrutura de novo módulo
 * 
 * Uso: node scripts/new-module.js <nome-do-modulo>
 * Exemplo: node scripts/new-module.js usuarios
 */

const fs = require('fs')
const path = require('path')
const readline = require('readline')

const MODULES_PATH = path.join(__dirname, '../apps/web/src/modules')

// Templates de arquivos
const templates = {
  'types.ts': (moduleName, pascalName) => `/**
 * Tipos do módulo ${pascalName}
 */

export interface ${pascalName}Item {
  id: string
  name: string
  createdAt: Date
  updatedAt: Date
}

export interface ${pascalName}Filters {
  search?: string
  page?: number
  limit?: number
}

export interface ${pascalName}State {
  items: ${pascalName}Item[]
  isLoading: boolean
  error: string | null
}
`,

  'index.ts': (moduleName, pascalName) => `// ${pascalName} Module exports
export { default as ${pascalName}Page } from './${pascalName}Page'
export * from './types'
export * from './components'
export * from './hooks'
`,

  [`Page.tsx`]: (moduleName, pascalName) => `import { useState } from 'react'
import { useAuth } from '@template/shared'
// import { use${pascalName}Data } from './hooks'

export default function ${pascalName}Page() {
  const { user } = useAuth()
  const [search, setSearch] = useState('')

  return (
    <div className="container mx-auto p-6">
      <header className="mb-6">
        <h1 className="text-2xl font-bold">${pascalName}</h1>
        <p className="text-muted-foreground">
          Bem-vindo ao módulo ${pascalName}
        </p>
      </header>

      <section className="rounded-lg border bg-card p-6">
        <div className="mb-4">
          <input
            type="text"
            placeholder="Buscar..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-md border px-3 py-2"
            aria-label="Buscar"
          />
        </div>

        <div className="text-center text-muted-foreground">
          <p>Implemente a listagem de {moduleName} aqui</p>
          <p className="text-sm mt-2">
            Usuário: {user?.name || 'Não autenticado'}
          </p>
        </div>
      </section>
    </div>
  )
}
`,

  'components/index.ts': (moduleName, pascalName) => `// ${pascalName} Components
// export { ${pascalName}Card } from './${pascalName}Card'
`,

  'hooks/index.ts': (moduleName, pascalName) => `// ${pascalName} Hooks
// export { use${pascalName}Data } from './use${pascalName}Data'
`,

  'services/index.ts': (moduleName, pascalName) => `// ${pascalName} Services
// export { ${moduleName}Service } from './${moduleName}.service'
`,
}

function toPascalCase(str) {
  return str
    .split('-')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join('')
}

function toKebabCase(str) {
  return str
    .replace(/([a-z])([A-Z])/g, '$1-$2')
    .replace(/\s+/g, '-')
    .toLowerCase()
}

async function prompt(question) {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  })

  return new Promise(resolve => {
    rl.question(question, answer => {
      rl.close()
      resolve(answer.trim())
    })
  })
}

async function main() {
  console.log('🚀 Criador de Módulos - AeroLab\n')

  // Obter nome do módulo
  let moduleName = process.argv[2]
  
  if (!moduleName) {
    moduleName = await prompt('Nome do módulo (kebab-case): ')
  }

  if (!moduleName) {
    console.error('❌ Nome do módulo é obrigatório')
    process.exit(1)
  }

  moduleName = toKebabCase(moduleName)
  const pascalName = toPascalCase(moduleName)
  const modulePath = path.join(MODULES_PATH, moduleName)

  // Verificar se já existe
  if (fs.existsSync(modulePath)) {
    console.error(`❌ Módulo "${moduleName}" já existe em ${modulePath}`)
    process.exit(1)
  }

  console.log(`\n📁 Criando módulo: ${moduleName}`)
  console.log(`   PascalCase: ${pascalName}`)
  console.log(`   Path: ${modulePath}\n`)

  // Criar diretórios
  const dirs = ['', 'components', 'hooks', 'services']
  for (const dir of dirs) {
    const dirPath = path.join(modulePath, dir)
    fs.mkdirSync(dirPath, { recursive: true })
    console.log(`   📂 ${dir || moduleName}/`)
  }

  // Criar arquivos
  for (const [fileName, templateFn] of Object.entries(templates)) {
    const actualFileName = fileName.replace('Page.tsx', `${pascalName}Page.tsx`)
    const filePath = path.join(modulePath, actualFileName)
    const content = templateFn(moduleName, pascalName)
    fs.writeFileSync(filePath, content)
    console.log(`   📄 ${actualFileName}`)
  }

  console.log('\n✅ Módulo criado com sucesso!')
  console.log('\n📝 Próximos passos:')
  console.log(`   1. Adicione a rota em apps/web/src/App.tsx:`)
  console.log(`      const ${pascalName}Page = lazy(() => import('./modules/${moduleName}/${pascalName}Page'))`)
  console.log(`      <Route path="/${moduleName}" element={<${pascalName}Page />} />`)
  console.log(`   2. Adicione ao menu em apps/web/src/navigation/map.ts (opcional)`)
  console.log(`   3. Implemente a lógica do módulo\n`)
}

main().catch(console.error)
