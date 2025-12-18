#!/usr/bin/env python3
"""
AeroLab Platform Validator - Release-Ready Validation Suite

Executa validação completa da plataforma:
- Factory validate
- Lint/Typecheck/Tests/Build
- API smoke tests
- E2E tests (opcional)
- Gera relatório em reports/

Uso:
    python scripts/validate_all.py
    python scripts/validate_all.py --mode light  # Pula E2E
    pnpm validate:all
"""

import subprocess
import sys
import os
import json
import time
import hashlib
import socket
import signal
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class Status(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    SKIP = "SKIP"
    WARN = "WARN"


@dataclass
class StepResult:
    name: str
    status: Status
    duration: float
    output: str = ""
    error: str = ""


@dataclass
class ValidationReport:
    timestamp: str = ""
    branch: str = ""
    commit_sha: str = ""
    node_version: str = ""
    pnpm_version: str = ""
    python_version: str = ""
    mode: str = "full"
    steps: list = field(default_factory=list)
    endpoints_tested: list = field(default_factory=list)
    openapi_hash: str = ""
    total_duration: float = 0.0
    overall_status: Status = Status.PASS


# Globals
ROOT_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = ROOT_DIR / "reports"
API_DIR = ROOT_DIR / "apps" / "api"
STUDIO_DIR = ROOT_DIR / "apps" / "studio"
report = ValidationReport()
log_lines: list[str] = []


def log(msg: str, level: str = "INFO"):
    """Log message to console and buffer."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    line = f"[{timestamp}] [{level}] {msg}"
    print(line)
    log_lines.append(line)


def get_python_cmd() -> str:
    """Detect Python command (Windows: py, Linux: python)."""
    if sys.platform == "win32":
        try:
            subprocess.run(["py", "--version"], capture_output=True, check=True)
            return "py"
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
    return "python"


def run_command(
    cmd: list[str],
    cwd: Optional[Path] = None,
    timeout: int = 300,
    env: Optional[dict] = None,
) -> tuple[int, str, str]:
    """Run command and return (exit_code, stdout, stderr)."""
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd or ROOT_DIR,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=full_env,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"Command timed out after {timeout}s"
    except FileNotFoundError as e:
        return -1, "", f"Command not found: {e}"
    except Exception as e:
        return -1, "", str(e)


def run_step(name: str, cmd: list[str], cwd: Optional[Path] = None, 
             env: Optional[dict] = None, allow_fail: bool = False) -> StepResult:
    """Run a validation step and record result."""
    log(f"▶ {name}")
    start = time.time()
    
    exit_code, stdout, stderr = run_command(cmd, cwd=cwd, env=env)
    duration = time.time() - start
    
    if exit_code == 0:
        status = Status.PASS
        log(f"  ✅ {name} - PASS ({duration:.1f}s)")
    elif allow_fail:
        status = Status.WARN
        log(f"  ⚠️ {name} - WARN ({duration:.1f}s)")
    else:
        status = Status.FAIL
        log(f"  ❌ {name} - FAIL ({duration:.1f}s)")
        if stderr:
            log(f"     Error: {stderr[:200]}")
    
    result = StepResult(
        name=name,
        status=status,
        duration=duration,
        output=stdout[:5000] if stdout else "",
        error=stderr[:2000] if stderr else "",
    )
    report.steps.append(result)
    return result


def get_git_info():
    """Get current branch and commit SHA."""
    try:
        _, branch, _ = run_command(["git", "branch", "--show-current"])
        report.branch = branch.strip()
        _, sha, _ = run_command(["git", "rev-parse", "--short", "HEAD"])
        report.commit_sha = sha.strip()
    except Exception:
        report.branch = "unknown"
        report.commit_sha = "unknown"


def get_versions():
    """Get Node, pnpm, Python versions."""
    try:
        _, out, _ = run_command(["node", "--version"])
        report.node_version = out.strip()
    except Exception:
        report.node_version = "N/A"
    
    try:
        _, out, _ = run_command(["pnpm", "--version"])
        report.pnpm_version = out.strip()
    except Exception:
        report.pnpm_version = "N/A"
    
    report.python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


def find_free_port() -> int:
    """Find a free port for API server."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


# ============================================================
# VALIDATION STEPS
# ============================================================

def step_factory_validate() -> StepResult:
    """Run Factory v1.1 validation."""
    python_cmd = get_python_cmd()
    return run_step(
        "Factory Validate",
        [python_cmd, "scripts/factory_validate.py"],
        cwd=ROOT_DIR,
    )


def step_lint() -> StepResult:
    """Run ESLint on frontend."""
    return run_step(
        "ESLint (Frontend)",
        ["pnpm", "lint"],
        cwd=ROOT_DIR,
        allow_fail=True,  # Lint warnings shouldn't block
    )


def step_typecheck() -> StepResult:
    """Run TypeScript typecheck."""
    return run_step(
        "TypeScript Typecheck",
        ["pnpm", "typecheck"],
        cwd=ROOT_DIR,
        allow_fail=True,
    )


def step_api_lint() -> StepResult:
    """Run Ruff on API."""
    python_cmd = get_python_cmd()
    return run_step(
        "Ruff Lint (API)",
        [python_cmd, "-m", "ruff", "check", "src/"],
        cwd=API_DIR,
        allow_fail=True,
    )


def step_api_format_check() -> StepResult:
    """Check API formatting."""
    python_cmd = get_python_cmd()
    return run_step(
        "Ruff Format Check (API)",
        [python_cmd, "-m", "ruff", "format", "--check", "src/"],
        cwd=API_DIR,
        allow_fail=True,
    )


def step_api_tests() -> StepResult:
    """Run pytest on API."""
    python_cmd = get_python_cmd()
    return run_step(
        "Pytest (API)",
        [python_cmd, "-m", "pytest", "tests/", "-v", "--tb=short", "-q"],
        cwd=API_DIR,
        env={"TESTING": "true", "JWT_SECRET": "test-secret-for-validation"},
    )


def step_build_studio() -> StepResult:
    """Build Studio frontend."""
    return run_step(
        "Build Studio",
        ["pnpm", "--filter", "@aerolab/studio", "build"],
        cwd=ROOT_DIR,
    )


def step_e2e_studio() -> StepResult:
    """Run Playwright E2E tests on Studio."""
    return run_step(
        "E2E Tests (Studio)",
        ["pnpm", "--filter", "@aerolab/studio", "test:e2e"],
        cwd=ROOT_DIR,
        env={"CI": "true"},
        allow_fail=True,
    )


def step_openapi_snapshot() -> StepResult:
    """Generate OpenAPI snapshot and save to reports."""
    log("▶ OpenAPI Snapshot")
    start = time.time()
    
    try:
        # Import TestClient and app
        sys.path.insert(0, str(API_DIR))
        os.environ["TESTING"] = "1"
        os.environ["JWT_SECRET"] = "test-secret"
        
        from fastapi.testclient import TestClient
        from server import app
        
        client = TestClient(app)
        response = client.get("/openapi.json")
        
        if response.status_code == 200:
            openapi_data = response.json()
            
            # Save snapshot
            REPORTS_DIR.mkdir(exist_ok=True)
            snapshot_path = REPORTS_DIR / "openapi.snapshot.json"
            with open(snapshot_path, "w", encoding="utf-8") as f:
                json.dump(openapi_data, f, indent=2)
            
            # Calculate hash
            content = json.dumps(openapi_data, sort_keys=True)
            report.openapi_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
            
            # Record endpoints
            paths = openapi_data.get("paths", {})
            for path, methods in paths.items():
                for method in methods.keys():
                    if method.upper() in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                        report.endpoints_tested.append(f"{method.upper()} {path}")
            
            duration = time.time() - start
            log(f"  ✅ OpenAPI Snapshot - PASS ({duration:.1f}s) - {len(paths)} paths, hash: {report.openapi_hash}")
            
            result = StepResult(
                name="OpenAPI Snapshot",
                status=Status.PASS,
                duration=duration,
                output=f"Saved to {snapshot_path}, {len(paths)} paths",
            )
        else:
            duration = time.time() - start
            log(f"  ❌ OpenAPI Snapshot - FAIL ({duration:.1f}s) - Status {response.status_code}")
            result = StepResult(
                name="OpenAPI Snapshot",
                status=Status.FAIL,
                duration=duration,
                error=f"Status {response.status_code}",
            )
    except Exception as e:
        duration = time.time() - start
        log(f"  ❌ OpenAPI Snapshot - FAIL ({duration:.1f}s) - {e}")
        result = StepResult(
            name="OpenAPI Snapshot",
            status=Status.FAIL,
            duration=duration,
            error=str(e),
        )
    
    report.steps.append(result)
    return result


def step_smoke_endpoints() -> StepResult:
    """Smoke test critical endpoints."""
    log("▶ Endpoint Smoke Tests")
    start = time.time()
    
    try:
        sys.path.insert(0, str(API_DIR))
        os.environ["TESTING"] = "1"
        os.environ["JWT_SECRET"] = "test-secret"
        
        from fastapi.testclient import TestClient
        from server import app
        
        client = TestClient(app)
        
        # Critical endpoints to test
        endpoints = [
            ("GET", "/health", [200]),
            ("GET", "/openapi.json", [200]),
            ("GET", "/docs", [200]),
            ("GET", "/api/v1/workflows/registry", [200, 401, 403]),
            ("GET", "/workflows/licitacoes-monitor/schema", [200]),
        ]
        
        passed = 0
        failed = 0
        results = []
        
        for method, path, expected_codes in endpoints:
            try:
                if method == "GET":
                    resp = client.get(path)
                elif method == "POST":
                    resp = client.post(path)
                else:
                    continue
                
                if resp.status_code in expected_codes:
                    passed += 1
                    results.append(f"  ✓ {method} {path} → {resp.status_code}")
                else:
                    failed += 1
                    results.append(f"  ✗ {method} {path} → {resp.status_code} (expected {expected_codes})")
            except Exception as e:
                failed += 1
                results.append(f"  ✗ {method} {path} → ERROR: {e}")
        
        duration = time.time() - start
        
        if failed == 0:
            status = Status.PASS
            log(f"  ✅ Endpoint Smoke Tests - PASS ({duration:.1f}s) - {passed}/{len(endpoints)}")
        else:
            status = Status.FAIL
            log(f"  ❌ Endpoint Smoke Tests - FAIL ({duration:.1f}s) - {passed}/{len(endpoints)}")
        
        for r in results:
            log(r)
        
        result = StepResult(
            name="Endpoint Smoke Tests",
            status=status,
            duration=duration,
            output="\n".join(results),
        )
    except Exception as e:
        duration = time.time() - start
        log(f"  ❌ Endpoint Smoke Tests - FAIL ({duration:.1f}s) - {e}")
        result = StepResult(
            name="Endpoint Smoke Tests",
            status=Status.FAIL,
            duration=duration,
            error=str(e),
        )
    
    report.steps.append(result)
    return result


# ============================================================
# REPORT GENERATION
# ============================================================

def generate_report():
    """Generate validation report markdown."""
    REPORTS_DIR.mkdir(exist_ok=True)
    
    # Calculate overall status
    fails = [s for s in report.steps if s.status == Status.FAIL]
    if fails:
        report.overall_status = Status.FAIL
    else:
        report.overall_status = Status.PASS
    
    # Generate markdown
    md = f"""# AeroLab Validation Report

> **Generated:** {report.timestamp}  
> **Mode:** {report.mode}  
> **Status:** {'✅ PASS' if report.overall_status == Status.PASS else '❌ FAIL'}

---

## Environment

| Item | Value |
|------|-------|
| Branch | `{report.branch}` |
| Commit | `{report.commit_sha}` |
| Node | `{report.node_version}` |
| pnpm | `{report.pnpm_version}` |
| Python | `{report.python_version}` |

---

## Validation Results

| Step | Status | Duration |
|------|--------|----------|
"""
    
    for step in report.steps:
        status_icon = {
            Status.PASS: "✅",
            Status.FAIL: "❌",
            Status.SKIP: "⏭️",
            Status.WARN: "⚠️",
        }.get(step.status, "❓")
        md += f"| {step.name} | {status_icon} {step.status.value} | {step.duration:.1f}s |\n"
    
    md += f"""
**Total Duration:** {report.total_duration:.1f}s

---

## OpenAPI Snapshot

- **Hash:** `{report.openapi_hash}`
- **File:** `reports/openapi.snapshot.json`
- **Endpoints:** {len(report.endpoints_tested)}

<details>
<summary>Endpoints List ({len(report.endpoints_tested)})</summary>

```
"""
    for ep in sorted(report.endpoints_tested)[:50]:
        md += f"{ep}\n"
    if len(report.endpoints_tested) > 50:
        md += f"... and {len(report.endpoints_tested) - 50} more\n"
    
    md += """```

</details>

---

## Reproduction Commands

```bash
# Run full validation
pnpm validate:all

# Run in light mode (skip E2E)
pnpm validate:all --mode light

# Individual commands
pnpm factory:validate
pnpm lint
pnpm typecheck
cd apps/api && pytest tests/ -v
pnpm --filter @aerolab/studio build
```

---

## Failures

"""
    
    if fails:
        for step in fails:
            md += f"""### {step.name}

```
{step.error[:1000] if step.error else 'No error details'}
```

"""
    else:
        md += "_No failures._\n"
    
    md += f"""
---

_Report generated by `scripts/validate_all.py` at {report.timestamp}_
"""
    
    # Write report
    report_path = REPORTS_DIR / "validation_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(md)
    
    # Write command log
    log_path = REPORTS_DIR / "commands.log"
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines))
    
    log(f"\n📄 Report saved to: {report_path}")
    log(f"📄 Log saved to: {log_path}")


def print_summary():
    """Print final summary to console."""
    print("\n" + "=" * 60)
    print("  VALIDATION SUMMARY")
    print("=" * 60)
    
    for step in report.steps:
        status_icon = {
            Status.PASS: "✅",
            Status.FAIL: "❌",
            Status.SKIP: "⏭️",
            Status.WARN: "⚠️",
        }.get(step.status, "❓")
        print(f"  {status_icon} {step.name}: {step.status.value} ({step.duration:.1f}s)")
    
    print("-" * 60)
    print(f"  Total Duration: {report.total_duration:.1f}s")
    print(f"  OpenAPI Hash: {report.openapi_hash}")
    print(f"  Endpoints: {len(report.endpoints_tested)}")
    print("=" * 60)
    
    if report.overall_status == Status.PASS:
        print("\n  🎉 VALIDATION PASSED\n")
        return 0
    else:
        print("\n  ❌ VALIDATION FAILED\n")
        return 1


# ============================================================
# MAIN
# ============================================================

def main():
    """Main entry point."""
    # Parse args
    mode = "full"
    if "--mode" in sys.argv:
        idx = sys.argv.index("--mode")
        if idx + 1 < len(sys.argv):
            mode = sys.argv[idx + 1]
    
    if os.environ.get("VALIDATE_MODE"):
        mode = os.environ["VALIDATE_MODE"]
    
    report.mode = mode
    report.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print("\n" + "=" * 60)
    print("  🏭 AeroLab Platform Validator")
    print(f"  Mode: {mode}")
    print("=" * 60 + "\n")
    
    start_time = time.time()
    
    # Gather info
    get_git_info()
    get_versions()
    
    log(f"Branch: {report.branch}")
    log(f"Commit: {report.commit_sha}")
    log(f"Python: {report.python_version}")
    log("")
    
    # Run validation steps
    step_factory_validate()
    step_lint()
    step_typecheck()
    step_api_lint()
    step_api_format_check()
    step_api_tests()
    step_openapi_snapshot()
    step_smoke_endpoints()
    
    # Build (can be slow)
    step_build_studio()
    
    # E2E (optional in light mode)
    if mode == "full":
        step_e2e_studio()
    else:
        log("⏭️ Skipping E2E tests (light mode)")
        report.steps.append(StepResult(
            name="E2E Tests (Studio)",
            status=Status.SKIP,
            duration=0,
            output="Skipped in light mode",
        ))
    
    # Finalize
    report.total_duration = time.time() - start_time
    
    generate_report()
    exit_code = print_summary()
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
