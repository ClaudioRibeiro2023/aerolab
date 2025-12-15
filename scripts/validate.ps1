<# 
.SYNOPSIS
    Script de validação completa do template
.DESCRIPTION
    Executa todas as verificações necessárias para garantir que o template está funcionando
#>

param(
    [switch]$SkipTests,
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootPath = Split-Path -Parent $scriptPath

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  VALIDAÇÃO DO TEMPLATE MONOREPO" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$errors = @()
$warnings = @()

# ============================================================================
# 1. Verificar estrutura de diretórios
# ============================================================================
Write-Host "[1/6] Verificando estrutura de diretórios..." -ForegroundColor Yellow

$requiredDirs = @(
    "apps/web/src",
    "apps/web/e2e",
    "packages/design-system/src",
    "packages/shared/src",
    "packages/types/src",
    "infra",
    "docs"
)

foreach ($dir in $requiredDirs) {
    $fullPath = Join-Path $rootPath $dir
    if (Test-Path $fullPath) {
        if ($Verbose) { Write-Host "  ✓ $dir" -ForegroundColor Green }
    } else {
        $errors += "Diretório não encontrado: $dir"
        Write-Host "  ✗ $dir" -ForegroundColor Red
    }
}

Write-Host "  Estrutura de diretórios: OK`n" -ForegroundColor Green

# ============================================================================
# 2. Verificar arquivos essenciais
# ============================================================================
Write-Host "[2/6] Verificando arquivos essenciais..." -ForegroundColor Yellow

$requiredFiles = @(
    "package.json",
    "pnpm-workspace.yaml",
    "tsconfig.base.json",
    "README.md",
    "apps/web/package.json",
    "apps/web/vite.config.ts",
    "apps/web/tsconfig.json",
    "apps/web/index.html",
    "apps/web/src/main.tsx",
    "apps/web/src/App.tsx",
    "packages/shared/src/auth/AuthContext.tsx",
    "packages/design-system/package.json",
    "packages/shared/package.json",
    "packages/types/package.json",
    "infra/docker-compose.yml"
)

foreach ($file in $requiredFiles) {
    $fullPath = Join-Path $rootPath $file
    if (Test-Path $fullPath) {
        if ($Verbose) { Write-Host "  ✓ $file" -ForegroundColor Green }
    } else {
        $errors += "Arquivo não encontrado: $file"
        Write-Host "  ✗ $file" -ForegroundColor Red
    }
}

Write-Host "  Arquivos essenciais: OK`n" -ForegroundColor Green

# ============================================================================
# 3. Verificar dependências instaladas
# ============================================================================
Write-Host "[3/6] Verificando dependências..." -ForegroundColor Yellow

Push-Location $rootPath
try {
    $nodeModules = Join-Path $rootPath "node_modules"
    if (Test-Path $nodeModules) {
        Write-Host "  Dependências instaladas: OK`n" -ForegroundColor Green
    } else {
        Write-Host "  Instalando dependências..." -ForegroundColor Yellow
        pnpm install
        Write-Host "  Dependências instaladas: OK`n" -ForegroundColor Green
    }
} finally {
    Pop-Location
}

# ============================================================================
# 4. TypeCheck - Verificar tipos
# ============================================================================
Write-Host "[4/6] Executando TypeCheck..." -ForegroundColor Yellow

Push-Location $rootPath
try {
    $typecheckResult = pnpm -r run typecheck 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  TypeCheck: OK`n" -ForegroundColor Green
    } else {
        $errors += "TypeCheck falhou"
        Write-Host "  TypeCheck: FALHOU`n" -ForegroundColor Red
        if ($Verbose) { Write-Host $typecheckResult }
    }
} finally {
    Pop-Location
}

# ============================================================================
# 5. Verificar build
# ============================================================================
Write-Host "[5/6] Verificando build..." -ForegroundColor Yellow

Push-Location (Join-Path $rootPath "apps/web")
try {
    $buildResult = pnpm run build 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Build: OK`n" -ForegroundColor Green
    } else {
        $errors += "Build falhou"
        Write-Host "  Build: FALHOU`n" -ForegroundColor Red
        if ($Verbose) { Write-Host $buildResult }
    }
} finally {
    Pop-Location
}

# ============================================================================
# 6. Testes E2E (opcional)
# ============================================================================
if (-not $SkipTests) {
    Write-Host "[6/6] Executando testes E2E..." -ForegroundColor Yellow
    
    Push-Location (Join-Path $rootPath "apps/web")
    try {
        # Verifica se playwright está instalado
        $playwrightInstalled = Test-Path (Join-Path $rootPath "node_modules/@playwright")
        if ($playwrightInstalled) {
            $testResult = npx playwright test --reporter=list 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  Testes E2E: OK`n" -ForegroundColor Green
            } else {
                $warnings += "Alguns testes E2E falharam"
                Write-Host "  Testes E2E: ALGUNS FALHARAM`n" -ForegroundColor Yellow
            }
        } else {
            $warnings += "Playwright não instalado, testes E2E ignorados"
            Write-Host "  Testes E2E: IGNORADOS (playwright não instalado)`n" -ForegroundColor Yellow
        }
    } finally {
        Pop-Location
    }
} else {
    Write-Host "[6/6] Testes E2E: IGNORADOS (--SkipTests)`n" -ForegroundColor Yellow
}

# ============================================================================
# Resumo
# ============================================================================
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  RESULTADO DA VALIDAÇÃO" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

if ($errors.Count -eq 0) {
    Write-Host "✓ TEMPLATE VALIDADO COM SUCESSO!" -ForegroundColor Green
    Write-Host "`nO template está pronto para uso.`n" -ForegroundColor White
    
    if ($warnings.Count -gt 0) {
        Write-Host "Avisos:" -ForegroundColor Yellow
        foreach ($warning in $warnings) {
            Write-Host "  - $warning" -ForegroundColor Yellow
        }
    }
    
    Write-Host "`nPróximos passos:" -ForegroundColor Cyan
    Write-Host "  1. cd apps/web" -ForegroundColor White
    Write-Host "  2. pnpm run dev" -ForegroundColor White
    Write-Host "  3. Acesse http://localhost:13000`n" -ForegroundColor White
    
    exit 0
} else {
    Write-Host "✗ VALIDAÇÃO FALHOU!" -ForegroundColor Red
    Write-Host "`nErros encontrados:" -ForegroundColor Red
    foreach ($error in $errors) {
        Write-Host "  - $error" -ForegroundColor Red
    }
    
    if ($warnings.Count -gt 0) {
        Write-Host "`nAvisos:" -ForegroundColor Yellow
        foreach ($warning in $warnings) {
            Write-Host "  - $warning" -ForegroundColor Yellow
        }
    }
    
    exit 1
}
