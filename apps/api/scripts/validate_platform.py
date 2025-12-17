#!/usr/bin/env python3
"""
AeroLab Platform - Complete Validation Script
Validates all endpoints, LLM integrations, and configurations
"""

import os
import sys
import json
import re
import asyncio
from pathlib import Path
from datetime import datetime

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()


class PlatformValidator:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "endpoints": [],
            "llm_providers": [],
            "env_variables": [],
            "frontend_pages": [],
            "errors": [],
            "warnings": []
        }
    
    def log(self, msg, level="INFO"):
        icons = {"INFO": "ℹ️", "OK": "✅", "WARN": "⚠️", "ERROR": "❌", "TEST": "🧪"}
        print(f"{icons.get(level, '•')} [{level}] {msg}")
    
    # =========================================================================
    # PHASE 1: Inventory
    # =========================================================================
    
    def inventory_endpoints(self):
        """Extract all endpoints from server.py"""
        self.log("Inventariando endpoints da API...", "INFO")
        
        server_path = Path(__file__).parent.parent / "server.py"
        if not server_path.exists():
            self.results["errors"].append("server.py not found")
            return []
        
        content = server_path.read_text(encoding="utf-8")
        
        # Find all route decorators
        pattern = r'@app\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']'
        matches = re.findall(pattern, content, re.IGNORECASE)
        
        endpoints = []
        for method, path in matches:
            endpoints.append({"method": method.upper(), "path": path})
        
        self.results["endpoints"] = endpoints
        self.log(f"Encontrados {len(endpoints)} endpoints", "OK")
        return endpoints
    
    def inventory_env_variables(self):
        """Extract all LLM-related env variables"""
        self.log("Inventariando variáveis de ambiente...", "INFO")
        
        llm_keys = {
            "GROQ_API_KEY": os.getenv("GROQ_API_KEY", ""),
            "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", ""),
            "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY", ""),
            "GOOGLE_API_KEY": os.getenv("GOOGLE_API_KEY", ""),
            "MISTRAL_API_KEY": os.getenv("MISTRAL_API_KEY", ""),
            "COHERE_API_KEY": os.getenv("COHERE_API_KEY", ""),
        }
        
        configured = []
        for key, value in llm_keys.items():
            status = "configured" if value and len(value) > 10 else "empty"
            configured.append({"key": key, "status": status, "length": len(value) if value else 0})
            if status == "configured":
                self.log(f"{key}: Configurado ({len(value)} chars)", "OK")
            else:
                self.log(f"{key}: Não configurado", "WARN")
        
        self.results["env_variables"] = configured
        return configured
    
    def inventory_frontend_pages(self):
        """List all frontend pages"""
        self.log("Inventariando páginas do frontend...", "INFO")
        
        studio_app = Path(__file__).parent.parent.parent / "studio" / "app"
        if not studio_app.exists():
            self.results["warnings"].append("Studio app folder not found")
            return []
        
        pages = []
        for page_file in studio_app.rglob("page.tsx"):
            route = "/" + str(page_file.parent.relative_to(studio_app)).replace("\\", "/")
            if route == "/.":
                route = "/"
            pages.append({"route": route, "file": str(page_file)})
        
        self.results["frontend_pages"] = pages
        self.log(f"Encontradas {len(pages)} páginas", "OK")
        return pages
    
    # =========================================================================
    # PHASE 2: LLM Integration Tests
    # =========================================================================
    
    async def test_groq(self):
        """Test Groq API"""
        key = os.getenv("GROQ_API_KEY", "")
        if not key or len(key) < 10:
            return {"provider": "groq", "status": "skipped", "reason": "No API key"}
        
        try:
            from groq import Groq
            client = Groq(api_key=key)
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": "Responda apenas: OK"}],
                max_tokens=10
            )
            response = completion.choices[0].message.content
            self.log(f"Groq (llama-3.3-70b): {response[:50]}", "OK")
            return {"provider": "groq", "status": "ok", "model": "llama-3.3-70b-versatile", "response": response}
        except Exception as e:
            self.log(f"Groq: {str(e)[:100]}", "ERROR")
            return {"provider": "groq", "status": "error", "error": str(e)}
    
    async def test_openai(self):
        """Test OpenAI API"""
        key = os.getenv("OPENAI_API_KEY", "")
        if not key or len(key) < 10:
            return {"provider": "openai", "status": "skipped", "reason": "No API key"}
        
        try:
            import openai
            client = openai.OpenAI(api_key=key)
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Responda apenas: OK"}],
                max_tokens=10
            )
            response = completion.choices[0].message.content
            self.log(f"OpenAI (gpt-4o-mini): {response[:50]}", "OK")
            return {"provider": "openai", "status": "ok", "model": "gpt-4o-mini", "response": response}
        except Exception as e:
            self.log(f"OpenAI: {str(e)[:100]}", "ERROR")
            return {"provider": "openai", "status": "error", "error": str(e)}
    
    async def test_anthropic(self):
        """Test Anthropic API"""
        key = os.getenv("ANTHROPIC_API_KEY", "")
        if not key or len(key) < 10:
            return {"provider": "anthropic", "status": "skipped", "reason": "No API key"}
        
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=key)
            message = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=10,
                messages=[{"role": "user", "content": "Responda apenas: OK"}]
            )
            response = message.content[0].text
            self.log(f"Anthropic (claude-3-haiku): {response[:50]}", "OK")
            return {"provider": "anthropic", "status": "ok", "model": "claude-3-haiku", "response": response}
        except Exception as e:
            self.log(f"Anthropic: {str(e)[:100]}", "ERROR")
            return {"provider": "anthropic", "status": "error", "error": str(e)}
    
    async def test_google(self):
        """Test Google Gemini API"""
        key = os.getenv("GOOGLE_API_KEY", "")
        if not key or len(key) < 10:
            return {"provider": "google", "status": "skipped", "reason": "No API key"}
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content("Responda apenas: OK")
            text = response.text
            self.log(f"Google (gemini-1.5-flash): {text[:50]}", "OK")
            return {"provider": "google", "status": "ok", "model": "gemini-1.5-flash", "response": text}
        except Exception as e:
            self.log(f"Google: {str(e)[:100]}", "ERROR")
            return {"provider": "google", "status": "error", "error": str(e)}
    
    async def test_mistral(self):
        """Test Mistral API"""
        key = os.getenv("MISTRAL_API_KEY", "")
        if not key or len(key) < 10:
            return {"provider": "mistral", "status": "skipped", "reason": "No API key"}
        
        try:
            from mistralai import Mistral
            client = Mistral(api_key=key)
            response = client.chat.complete(
                model="mistral-small-latest",
                messages=[{"role": "user", "content": "Responda apenas: OK"}]
            )
            text = response.choices[0].message.content
            self.log(f"Mistral (mistral-small): {text[:50]}", "OK")
            return {"provider": "mistral", "status": "ok", "model": "mistral-small", "response": text}
        except Exception as e:
            self.log(f"Mistral: {str(e)[:100]}", "ERROR")
            return {"provider": "mistral", "status": "error", "error": str(e)}
    
    async def test_cohere(self):
        """Test Cohere API"""
        key = os.getenv("COHERE_API_KEY", "")
        if not key or len(key) < 10:
            return {"provider": "cohere", "status": "skipped", "reason": "No API key"}
        
        try:
            import cohere
            client = cohere.Client(api_key=key)
            response = client.chat(
                model="command-r",
                message="Responda apenas: OK"
            )
            text = response.text
            self.log(f"Cohere (command-r): {text[:50]}", "OK")
            return {"provider": "cohere", "status": "ok", "model": "command-r", "response": text}
        except Exception as e:
            self.log(f"Cohere: {str(e)[:100]}", "ERROR")
            return {"provider": "cohere", "status": "error", "error": str(e)}
    
    async def test_all_llms(self):
        """Test all configured LLM providers"""
        self.log("Testando todos os provedores LLM...", "TEST")
        
        results = await asyncio.gather(
            self.test_groq(),
            self.test_openai(),
            self.test_anthropic(),
            self.test_google(),
            self.test_mistral(),
            self.test_cohere(),
            return_exceptions=True
        )
        
        self.results["llm_providers"] = [r if isinstance(r, dict) else {"error": str(r)} for r in results]
        
        ok_count = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "ok")
        self.log(f"LLMs funcionando: {ok_count}/6", "INFO")
        
        return results
    
    # =========================================================================
    # PHASE 3: API Endpoint Tests
    # =========================================================================
    
    async def test_endpoints(self, base_url="http://localhost:8000"):
        """Test all API endpoints"""
        import httpx
        
        self.log("Testando endpoints da API...", "TEST")
        
        test_cases = [
            ("GET", "/health", None, 200),
            ("GET", "/health/live", None, 200),
            ("GET", "/health/ready", None, 200),
            ("GET", "/agents", None, 200),
            ("GET", "/teams", None, 200),
            ("GET", "/workflows", None, 200),
            ("GET", "/rag/collections", None, 200),
            ("GET", "/logs", None, 200),
            ("GET", "/models", None, 200),
            ("GET", "/domains", None, 200),
            ("POST", "/auth/login", {"username": "admin"}, 200),
            ("POST", "/agents/Test/run", {"prompt": "Diga OK", "model": "llama-3.3-70b-versatile"}, 200),
        ]
        
        results = []
        async with httpx.AsyncClient(timeout=30.0) as client:
            for method, path, body, expected in test_cases:
                try:
                    if method == "GET":
                        r = await client.get(f"{base_url}{path}")
                    else:
                        r = await client.post(f"{base_url}{path}", json=body)
                    
                    status = "ok" if r.status_code == expected else "fail"
                    icon = "✅" if status == "ok" else "❌"
                    print(f"  {icon} {method} {path} -> {r.status_code}")
                    results.append({
                        "method": method,
                        "path": path,
                        "status_code": r.status_code,
                        "expected": expected,
                        "status": status
                    })
                except Exception as e:
                    print(f"  ❌ {method} {path} -> ERROR: {str(e)[:50]}")
                    results.append({
                        "method": method,
                        "path": path,
                        "status": "error",
                        "error": str(e)
                    })
        
        ok_count = sum(1 for r in results if r.get("status") == "ok")
        self.log(f"Endpoints OK: {ok_count}/{len(test_cases)}", "INFO")
        
        return results
    
    # =========================================================================
    # Main Execution
    # =========================================================================
    
    async def run_full_validation(self):
        """Execute complete platform validation"""
        print("\n" + "="*60)
        print("🚀 AeroLab Platform - Validação Completa")
        print("="*60 + "\n")
        
        # Phase 1: Inventory
        print("\n📋 FASE 1: Diagnóstico")
        print("-"*40)
        self.inventory_endpoints()
        self.inventory_env_variables()
        self.inventory_frontend_pages()
        
        # Phase 2: LLM Tests
        print("\n🧠 FASE 2: Teste de LLMs")
        print("-"*40)
        await self.test_all_llms()
        
        # Phase 3: API Tests
        print("\n🔌 FASE 3: Teste de Endpoints")
        print("-"*40)
        await self.test_endpoints()
        
        # Summary
        print("\n" + "="*60)
        print("📊 RESUMO DA VALIDAÇÃO")
        print("="*60)
        
        endpoints_ok = len([e for e in self.results.get("endpoints", [])])
        llms_ok = len([l for l in self.results.get("llm_providers", []) if l.get("status") == "ok"])
        pages_ok = len(self.results.get("frontend_pages", []))
        
        print(f"  • Endpoints mapeados: {endpoints_ok}")
        print(f"  • LLMs funcionando: {llms_ok}/6")
        print(f"  • Páginas frontend: {pages_ok}")
        print(f"  • Erros: {len(self.results.get('errors', []))}")
        print(f"  • Avisos: {len(self.results.get('warnings', []))}")
        
        # Save report
        report_path = Path(__file__).parent / "validation_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        print(f"\n📄 Relatório salvo em: {report_path}")
        
        return self.results


if __name__ == "__main__":
    validator = PlatformValidator()
    asyncio.run(validator.run_full_validation())
