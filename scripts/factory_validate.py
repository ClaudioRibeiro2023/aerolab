#!/usr/bin/env python3
"""
Factory Validate - Validador de repositório para Factory v1.1

Regras de validação:
- MD_LOCATION: Arquivos .md apenas em docs/ (exceto README.md raiz e em módulos Python)
- WORKFLOW_README: Cada workflow tem README.md
- WORKFLOW_SCHEMAS: Cada workflow tem input.json e result.json
- GOLDEN_TESTS: Mínimo 5 golden cases por workflow
- STATE_DEFAULTS: Template Flow Studio tem state_defaults.result
- RUNNER_EXISTS: Runner Python existe (warning)

Uso:
    python scripts/factory_validate.py
    pnpm factory:validate
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Severity(Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"


@dataclass
class ValidationResult:
    rule: str
    passed: bool
    severity: Severity
    message: str
    details: list[str]


def get_repo_root() -> Path:
    """Encontra a raiz do repositório."""
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    return Path(__file__).resolve().parent.parent


def validate_md_location(root: Path) -> ValidationResult:
    """Verifica se arquivos .md estão apenas em docs/ (exceto README.md e arquivos padrão)."""
    violations: list[str] = []
    
    allowed_paths = [
        root / "docs",
        root / "windsurf",
        root / "infra",
        root / ".github",
        root / ".windsurf",
        root / "apps" / "api" / "src",  # Permite docs técnicas inline
        root / "apps" / "api" / "data",
    ]
    
    # Arquivos .md permitidos em qualquer lugar
    allowed_names = {
        "README.md",
        "CHANGELOG.md",
        "CONTRIBUTING.md",
        "LICENSE.md",
        "CODE_OF_CONDUCT.md",
        "SECURITY.md",
        "ARCHITECTURE.md",
        "PLAYBOOK_OPERACAO.md",
    }
    
    for md_file in root.rglob("*.md"):
        # Ignorar pastas especiais
        path_str = str(md_file)
        if any(skip in path_str for skip in ["node_modules", ".git", "__pycache__", ".venv", "venv", "reports"]):
            continue
            
        # Permitir arquivos com nomes padrão
        if md_file.name in allowed_names:
            continue
        
        # Verificar se está em local permitido
        in_allowed = False
        for allowed in allowed_paths:
            try:
                md_file.relative_to(allowed)
                in_allowed = True
                break
            except ValueError:
                pass
            
        if not in_allowed:
            violations.append(str(md_file.relative_to(root)))
    
    return ValidationResult(
        rule="MD_LOCATION",
        passed=len(violations) == 0,
        severity=Severity.ERROR,
        message="Arquivos .md devem estar em docs/ ou windsurf/",
        details=violations,
    )


def validate_workflow_readme(root: Path) -> ValidationResult:
    """Verifica se cada workflow tem README.md."""
    violations: list[str] = []
    workflows_dir = root / "docs" / "workflows"
    
    if not workflows_dir.exists():
        return ValidationResult(
            rule="WORKFLOW_README",
            passed=True,
            severity=Severity.ERROR,
            message="Cada workflow deve ter README.md",
            details=["Nenhum workflow encontrado"],
        )
    
    for workflow_dir in workflows_dir.iterdir():
        if workflow_dir.is_dir():
            readme = workflow_dir / "README.md"
            if not readme.exists():
                violations.append(workflow_dir.name)
    
    return ValidationResult(
        rule="WORKFLOW_README",
        passed=len(violations) == 0,
        severity=Severity.ERROR,
        message="Cada workflow deve ter README.md",
        details=violations,
    )


def validate_workflow_schemas(root: Path) -> ValidationResult:
    """Verifica se cada workflow tem input.json e result.json."""
    violations: list[str] = []
    workflows_dir = root / "docs" / "workflows"
    
    if not workflows_dir.exists():
        return ValidationResult(
            rule="WORKFLOW_SCHEMAS",
            passed=True,
            severity=Severity.ERROR,
            message="Cada workflow deve ter schemas/input.json e schemas/result.json",
            details=[],
        )
    
    for workflow_dir in workflows_dir.iterdir():
        if workflow_dir.is_dir():
            schemas_dir = workflow_dir / "schemas"
            input_schema = schemas_dir / "input.json"
            result_schema = schemas_dir / "result.json"
            
            if not input_schema.exists():
                violations.append(f"{workflow_dir.name}: falta input.json")
            if not result_schema.exists():
                violations.append(f"{workflow_dir.name}: falta result.json")
    
    return ValidationResult(
        rule="WORKFLOW_SCHEMAS",
        passed=len(violations) == 0,
        severity=Severity.ERROR,
        message="Cada workflow deve ter schemas/input.json e schemas/result.json",
        details=violations,
    )


def validate_golden_tests(root: Path) -> ValidationResult:
    """Verifica se cada workflow tem mínimo 5 golden cases."""
    violations: list[str] = []
    golden_dir = root / "apps" / "api" / "tests" / "golden"
    workflows_dir = root / "docs" / "workflows"
    
    if not workflows_dir.exists():
        return ValidationResult(
            rule="GOLDEN_TESTS",
            passed=True,
            severity=Severity.ERROR,
            message="Cada workflow deve ter mínimo 5 golden cases",
            details=[],
        )
    
    for workflow_dir in workflows_dir.iterdir():
        if workflow_dir.is_dir():
            slug = workflow_dir.name
            tests_dir = golden_dir / slug
            
            if not tests_dir.exists():
                violations.append(f"{slug}: pasta de testes não existe")
                continue
            
            cases = list(tests_dir.glob("case_*.json"))
            if len(cases) < 5:
                violations.append(f"{slug}: apenas {len(cases)} casos (mínimo: 5)")
    
    return ValidationResult(
        rule="GOLDEN_TESTS",
        passed=len(violations) == 0,
        severity=Severity.ERROR,
        message="Cada workflow deve ter mínimo 5 golden cases",
        details=violations,
    )


def validate_state_defaults(root: Path) -> ValidationResult:
    """Verifica se templates Flow Studio têm state_defaults.result."""
    violations: list[str] = []
    templates_dir = root / "apps" / "api" / "src" / "flow_studio" / "templates"
    
    if not templates_dir.exists():
        return ValidationResult(
            rule="STATE_DEFAULTS",
            passed=True,
            severity=Severity.ERROR,
            message="Templates Flow Studio devem ter state_defaults.result",
            details=[],
        )
    
    for template_file in templates_dir.rglob("*.json"):
        try:
            with open(template_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            state_defaults = data.get("state_defaults", {})
            result = state_defaults.get("result", {})
            
            required_fields = ["status", "payload_json", "errors"]
            missing = [f for f in required_fields if f not in result]
            
            if missing:
                rel_path = template_file.relative_to(root)
                violations.append(f"{rel_path}: falta {', '.join(missing)} em state_defaults.result")
        except json.JSONDecodeError:
            violations.append(f"{template_file.name}: JSON inválido")
        except Exception as e:
            violations.append(f"{template_file.name}: erro ao ler ({e})")
    
    return ValidationResult(
        rule="STATE_DEFAULTS",
        passed=len(violations) == 0,
        severity=Severity.ERROR,
        message="Templates Flow Studio devem ter state_defaults.result",
        details=violations,
    )


def validate_runner_exists(root: Path) -> ValidationResult:
    """Verifica se cada workflow tem runner Python."""
    violations: list[str] = []
    workflows_dir = root / "docs" / "workflows"
    runners_base = root / "apps" / "api" / "src" / "workflows"
    
    if not workflows_dir.exists():
        return ValidationResult(
            rule="RUNNER_EXISTS",
            passed=True,
            severity=Severity.WARNING,
            message="Cada workflow deve ter runner.py implementado",
            details=[],
        )
    
    for workflow_dir in workflows_dir.iterdir():
        if workflow_dir.is_dir():
            slug = workflow_dir.name
            
            # Buscar runner em qualquer domínio
            found = False
            for domain_dir in runners_base.iterdir():
                if domain_dir.is_dir():
                    runner_dir = domain_dir / slug
                    if (runner_dir / "runner.py").exists():
                        found = True
                        break
            
            if not found:
                violations.append(slug)
    
    return ValidationResult(
        rule="RUNNER_EXISTS",
        passed=len(violations) == 0,
        severity=Severity.WARNING,
        message="Cada workflow deve ter runner.py implementado",
        details=violations,
    )


def print_result(result: ValidationResult, verbose: bool = True) -> None:
    """Imprime resultado de uma validação."""
    status = "✅" if result.passed else ("⚠️" if result.severity == Severity.WARNING else "❌")
    print(f"  {status} {result.rule}: {'OK' if result.passed else 'FAIL'}")
    
    if not result.passed and verbose and result.details:
        for detail in result.details[:5]:
            print(f"     → {detail}")
        if len(result.details) > 5:
            print(f"     ... e mais {len(result.details) - 5} violações")


def main() -> int:
    """Executa todas as validações."""
    root = get_repo_root()
    
    print(f"\n🏭 Factory Validate v1.1")
    print(f"   Repositório: {root}\n")
    
    validators = [
        validate_md_location,
        validate_workflow_readme,
        validate_workflow_schemas,
        validate_golden_tests,
        validate_state_defaults,
        validate_runner_exists,
    ]
    
    results: list[ValidationResult] = []
    for validator in validators:
        result = validator(root)
        results.append(result)
        print_result(result)
    
    # Calcular resultado final
    errors = [r for r in results if not r.passed and r.severity == Severity.ERROR]
    warnings = [r for r in results if not r.passed and r.severity == Severity.WARNING]
    
    print()
    if errors:
        print(f"❌ factory:validate FAIL ({len(errors)} errors, {len(warnings)} warnings)")
        return 1
    elif warnings:
        print(f"⚠️ factory:validate PASS with warnings ({len(warnings)} warnings)")
        return 0
    else:
        print(f"✅ factory:validate PASS")
        return 0


if __name__ == "__main__":
    sys.exit(main())
