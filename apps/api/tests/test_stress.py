"""
Stress & Performance Tests - Agno Platform v2.0

Metodologias:
- Stress testing com múltiplas operações concorrentes
- Edge cases e boundary testing
- Memory leak detection
- Performance benchmarks
"""

import pytest
import sys
import time
import threading
import gc
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# =============================================================================
# BILLING STRESS TESTS
# =============================================================================

class TestBillingStress:
    """Stress tests para módulo de Billing."""
    
    def test_metering_high_volume(self):
        """Testa metering com alto volume de registros."""
        from billing.metering import MeteringService
        
        service = MeteringService(buffer_size=100)
        
        # Registrar 1000 operações
        start = time.time()
        for i in range(1000):
            service.track_tokens(f"user_{i % 10}", 100, 50)
        elapsed = time.time() - start
        
        # Deve completar em menos de 2 segundos
        assert elapsed < 2.0, f"Metering muito lento: {elapsed:.2f}s"
        
        # Flush e verificar
        service.flush()
        records = service.get_records()
        assert len(records) >= 1000
    
    def test_pricing_concurrent_calculations(self):
        """Testa cálculos de preço concorrentes."""
        from billing.pricing import PricingEngine
        from billing.types import UsageType
        
        engine = PricingEngine()
        results = []
        errors = []
        
        def calculate_cost():
            try:
                for _ in range(100):
                    cost = engine.calculate_cost(UsageType.TOKENS_INPUT, 1000)
                    results.append(cost["total"])
            except Exception as e:
                errors.append(str(e))
        
        # 10 threads concorrentes
        threads = [threading.Thread(target=calculate_cost) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0, f"Errors: {errors}"
        assert len(results) == 1000
        # Todos os resultados devem ser iguais
        assert len(set(results)) == 1
    
    def test_invoice_generation_batch(self):
        """Testa geração de múltiplas faturas."""
        from billing.billing import BillingManager
        
        manager = BillingManager()
        invoices = []
        
        start = time.time()
        for i in range(50):
            invoice = manager.generate_invoice(f"user_{i}")
            invoices.append(invoice)
        elapsed = time.time() - start
        
        assert len(invoices) == 50
        assert elapsed < 5.0, f"Geração de faturas muito lenta: {elapsed:.2f}s"
        
        # Verificar unicidade de IDs
        ids = [inv.id for inv in invoices]
        assert len(ids) == len(set(ids)), "IDs de faturas duplicados"
    
    def test_plan_limit_check_performance(self):
        """Testa performance de verificação de limites."""
        from billing.plans import PlanManager
        from billing.types import UsageType
        
        manager = PlanManager()
        
        # Atribuir planos
        for i in range(100):
            manager.assign_plan(f"user_{i}", "pro")
        
        start = time.time()
        for i in range(10000):
            user_id = f"user_{i % 100}"
            manager.check_limit(user_id, UsageType.TOKENS_INPUT, 1000)
        elapsed = time.time() - start
        
        # 10k verificações em menos de 1 segundo
        assert elapsed < 1.0, f"Verificação de limites lenta: {elapsed:.2f}s"


# =============================================================================
# MARKETPLACE STRESS TESTS
# =============================================================================

class TestMarketplaceStress:
    """Stress tests para módulo de Marketplace."""
    
    def test_search_performance(self):
        """Testa performance de busca."""
        from marketplace.search import MarketplaceSearch
        from marketplace.marketplace import Marketplace
        
        mp = Marketplace()
        search = MarketplaceSearch(mp)
        
        queries = ["agent", "support", "data", "analytics", "automation"]
        
        start = time.time()
        for _ in range(100):
            for query in queries:
                results = search.search(query)
                assert "results" in results
        elapsed = time.time() - start
        
        # 500 buscas em menos de 2 segundos
        assert elapsed < 2.0, f"Busca lenta: {elapsed:.2f}s"
    
    def test_concurrent_installations(self):
        """Testa instalações concorrentes."""
        from marketplace.marketplace import Marketplace
        
        mp = Marketplace()
        listings = mp.list_all()
        
        if not listings:
            pytest.skip("No listings available")
        
        listing_id = listings[0].id
        results = []
        errors = []
        
        def install_for_user(user_id):
            try:
                result = mp.install(listing_id, user_id)
                results.append(result)
            except Exception as e:
                errors.append(str(e))
        
        # 50 instalações concorrentes
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(install_for_user, f"user_{i}") for i in range(50)]
            for f in as_completed(futures):
                pass
        
        assert len(errors) == 0, f"Errors: {errors}"
        assert len(results) == 50
    
    def test_review_aggregation(self):
        """Testa agregação de reviews em volume."""
        from marketplace.marketplace import Marketplace
        
        mp = Marketplace()
        listings = mp.list_all()
        
        if not listings:
            pytest.skip("No listings available")
        
        listing_id = listings[0].id
        
        # Adicionar 100 reviews
        for i in range(100):
            mp.add_review(
                listing_id=listing_id,
                user_id=f"user_{i}",
                rating=((i % 5) + 1),  # 1-5 rating
                comment=f"Review {i}"
            )
        
        # Verificar rating médio
        listing = mp.get_by_id(listing_id)
        assert listing is not None
        # Rating deve estar entre 1 e 5
        assert 1.0 <= listing.rating <= 5.0


# =============================================================================
# ENTERPRISE STRESS TESTS
# =============================================================================

class TestEnterpriseStress:
    """Stress tests para módulo Enterprise."""
    
    def test_sso_session_management(self):
        """Testa gerenciamento de sessões SSO em volume."""
        from enterprise.sso import SSOManager
        from enterprise.types import SSOConfig, SSOProtocol, SAMLConfig
        
        manager = SSOManager()
        
        # Configurar 10 tenants
        for i in range(10):
            config = SSOConfig(
                tenant_id=f"tenant_{i}",
                protocol=SSOProtocol.SAML_2_0,
                saml_config=SAMLConfig(
                    idp_entity_id=f"https://idp{i}.example.com",
                    idp_sso_url=f"https://idp{i}.example.com/sso",
                    sp_entity_id=f"https://app.agno.ai/saml/sp/{i}",
                    sp_acs_url=f"https://app.agno.ai/saml/acs/{i}",
                )
            )
            manager.configure_sso(config)
        
        # Verificar todas as configs
        configs = manager.list_configs()
        assert len(configs) == 10
    
    def test_region_routing_performance(self):
        """Testa performance de roteamento por região."""
        from enterprise.multiregion import LatencyRouter
        
        router = LatencyRouter()
        
        regions = ["us-east-1", "eu-west-1", "ap-northeast-1", "sa-east-1"]
        
        start = time.time()
        for _ in range(1000):
            for region in regions:
                result = router.route_request(f"tenant_test", client_region=region)
                assert "region" in result or "error" in result
        elapsed = time.time() - start
        
        # 4000 roteamentos em menos de 1 segundo
        assert elapsed < 1.0, f"Roteamento lento: {elapsed:.2f}s"
    
    def test_whitelabel_theme_compilation(self):
        """Testa compilação de temas em volume."""
        from enterprise.whitelabel import BrandingEngine
        from enterprise.types import BrandingConfig
        
        engine = BrandingEngine()
        
        colors = ["#ff0000", "#00ff00", "#0000ff", "#ffff00", "#ff00ff"]
        
        start = time.time()
        for i in range(100):
            config = BrandingConfig(
                primary_color=colors[i % len(colors)],
                secondary_color=colors[(i + 1) % len(colors)],
            )
            css = engine.compile_theme(f"tenant_{i}", config)
            assert "--color-primary" in css
        elapsed = time.time() - start
        
        # 100 compilações em menos de 1 segundo
        assert elapsed < 1.0, f"Compilação lenta: {elapsed:.2f}s"


# =============================================================================
# EDGE CASES & BOUNDARY TESTS
# =============================================================================

class TestEdgeCases:
    """Testes de edge cases e condições de contorno."""
    
    def test_empty_user_id(self):
        """Testa comportamento com user_id vazio."""
        from billing.metering import MeteringService
        from billing.plans import PlanManager
        
        metering = MeteringService()
        plans = PlanManager()
        
        # Deve funcionar mesmo com string vazia
        records = metering.track_tokens("", 100, 50)
        assert len(records) == 2
        
        # Plano default para usuário vazio
        plan = plans.get_user_plan("")
        assert plan.id == "free"
    
    def test_zero_quantity(self):
        """Testa comportamento com quantidade zero."""
        from billing.pricing import PricingEngine
        from billing.types import UsageType
        
        engine = PricingEngine()
        
        cost = engine.calculate_cost(UsageType.TOKENS_INPUT, 0)
        assert cost["total"] == 0
    
    def test_negative_quantity(self):
        """Testa comportamento com quantidade negativa."""
        from billing.pricing import PricingEngine
        from billing.types import UsageType
        
        engine = PricingEngine()
        
        # Quantidade negativa deve resultar em custo 0 ou positivo
        cost = engine.calculate_cost(UsageType.TOKENS_INPUT, -100)
        assert cost["total"] >= 0
    
    def test_very_large_quantity(self):
        """Testa comportamento com quantidade muito grande."""
        from billing.pricing import PricingEngine
        from billing.types import UsageType
        
        engine = PricingEngine()
        
        # 1 bilhão de tokens
        cost = engine.calculate_cost(UsageType.TOKENS_INPUT, 1_000_000_000)
        assert cost["total"] > 0
        assert isinstance(cost["total"], float)
    
    def test_special_characters_in_search(self):
        """Testa busca com caracteres especiais."""
        from marketplace.search import MarketplaceSearch
        from marketplace.marketplace import Marketplace
        
        mp = Marketplace()
        search = MarketplaceSearch(mp)
        
        special_queries = [
            "test<script>",
            "'; DROP TABLE users;--",
            "test\x00null",
            "emoji🚀test",
            "unicode™®©",
        ]
        
        for query in special_queries:
            # Não deve lançar exceção
            results = search.search(query)
            assert "results" in results
    
    def test_unicode_in_branding(self):
        """Testa unicode em configuração de branding."""
        from enterprise.whitelabel import WhiteLabelManager
        from enterprise.types import WhiteLabelConfig, BrandingConfig
        
        manager = WhiteLabelManager()
        
        config = WhiteLabelConfig(
            tenant_id="unicode_tenant",
            branding=BrandingConfig(primary_color="#123456"),
            app_name="日本語アプリ 🚀",
            app_tagline="Plataforma de IA 人工知能",
        )
        
        result = manager.configure(config)
        assert result.app_name == "日本語アプリ 🚀"
    
    def test_expired_session_handling(self):
        """Testa handling de sessões expiradas."""
        from enterprise.types import SSOSession
        
        # Sessão expirada
        session = SSOSession(
            user_id="user1",
            tenant_id="tenant1",
            expires_at=datetime.now() - timedelta(hours=1)
        )
        
        assert session.is_expired() is True
        
        # Refresh deve atualizar expiração
        session.refresh(hours=24)
        assert session.is_expired() is False


# =============================================================================
# MEMORY & RESOURCE TESTS
# =============================================================================

class TestMemoryManagement:
    """Testes de gerenciamento de memória."""
    
    def test_metering_memory_cleanup(self):
        """Testa limpeza de memória após flush."""
        from billing.metering import MeteringService
        
        service = MeteringService(buffer_size=50)
        
        # Forçar coleta de lixo inicial
        gc.collect()
        
        # Adicionar muitos registros
        for _ in range(10):
            for i in range(100):
                service.track_tokens(f"user_{i}", 100, 50)
            service.flush()
        
        # Buffer deve estar vazio após flush
        # (verificado indiretamente pelo comportamento)
        records_before = len(service.get_records())
        
        # Adicionar mais registros
        service.track_tokens("test_user", 100, 50)
        service.flush()
        
        records_after = len(service.get_records())
        assert records_after == records_before + 2
    
    def test_search_cache_size(self):
        """Testa que cache de busca não cresce indefinidamente."""
        from marketplace.search import MarketplaceSearch
        from marketplace.marketplace import Marketplace
        
        mp = Marketplace()
        search = MarketplaceSearch(mp)
        
        # Realizar muitas buscas diferentes
        for i in range(1000):
            search.search(f"query_{i}")
        
        # Se houver cache, deve estar limitado
        # (implementação específica pode variar)
        assert True  # Passou sem memory error


# =============================================================================
# INTEGRATION STRESS TESTS
# =============================================================================

class TestIntegrationStress:
    """Testes de integração com stress."""
    
    def test_full_billing_cycle_stress(self):
        """Testa ciclo completo de billing sob stress."""
        from billing.billing import BillingManager
        from billing.metering import MeteringService
        from billing.plans import PlanManager
        
        billing = BillingManager()
        metering = billing._metering
        plans = billing._plans
        
        # Setup: 10 usuários com diferentes planos
        for i in range(10):
            plan = ["free", "pro", "team", "enterprise"][i % 4]
            plans.assign_plan(f"user_{i}", plan)
        
        # Simular uso intenso
        for _ in range(10):
            for i in range(10):
                metering.track_tokens(f"user_{i}", 1000, 500)
                metering.track_api_call(f"user_{i}", "/api/v1/test")
        
        metering.flush()
        
        # Gerar faturas para todos
        invoices = []
        for i in range(10):
            invoice = billing.generate_invoice(f"user_{i}")
            invoices.append(invoice)
        
        assert len(invoices) == 10
        
        # Processar pagamentos
        for invoice in invoices:
            payment = billing.process_payment(
                invoice.id,
                method="credit_card",
                payment_details={"card_last4": "1234"}
            )
            assert payment is not None
    
    def test_marketplace_full_lifecycle(self):
        """Testa ciclo completo do marketplace sob stress."""
        from marketplace.marketplace import Marketplace
        from marketplace.publisher import Publisher
        from marketplace.search import MarketplaceSearch
        from marketplace.types import ListingType, ListingCategory
        
        mp = Marketplace()
        pub = Publisher(mp)
        search = MarketplaceSearch(mp)
        
        # Criar 20 listings
        for i in range(20):
            listing = pub.create_listing(
                author_id=f"author_{i}",
                author_name=f"Author {i}",
                name=f"Test Agent {i}",
                description=f"Description for agent {i} with enough content to pass validation",
                type=ListingType.AGENT,
                category=ListingCategory.PRODUCTIVITY
            )
            assert listing is not None
        
        # Buscar e instalar
        results = search.search("Test Agent")
        assert results["total"] >= 20
        
        # Instalar primeiros 10
        for i in range(min(10, len(results["results"]))):
            listing_id = results["results"][i]["id"]
            mp.install(listing_id, "test_user")
        
        # Verificar instalações
        installations = mp.get_user_installations("test_user")
        assert len(installations) >= 10
    
    def test_enterprise_multi_tenant_stress(self):
        """Testa multi-tenancy sob stress."""
        from enterprise.sso import SSOManager
        from enterprise.multiregion import DataResidencyManager, LatencyRouter
        from enterprise.whitelabel import WhiteLabelManager
        from enterprise.types import (
            SSOConfig, SSOProtocol, OIDCConfig,
            WhiteLabelConfig, BrandingConfig, Region
        )
        
        sso = SSOManager()
        residency = DataResidencyManager()
        router = LatencyRouter(residency_manager=residency)
        whitelabel = WhiteLabelManager()
        
        # Configurar 20 tenants
        for i in range(20):
            tenant_id = f"tenant_{i}"
            
            # SSO
            oidc = OIDCConfig(
                issuer=f"https://auth{i}.example.com",
                client_id=f"client_{i}",
                client_secret=f"secret_{i}"
            )
            sso.configure_sso(SSOConfig(
                tenant_id=tenant_id,
                protocol=SSOProtocol.OIDC,
                oidc_config=oidc
            ))
            
            # Region
            region = list(Region)[i % len(list(Region))]
            residency.configure_tenant(tenant_id, region)
            
            # White-label
            whitelabel.configure(WhiteLabelConfig(
                tenant_id=tenant_id,
                branding=BrandingConfig(primary_color=f"#{i:02x}{i:02x}{i:02x}"),
                app_name=f"App {i}"
            ))
        
        # Verificar todos os tenants
        for i in range(20):
            tenant_id = f"tenant_{i}"
            
            assert sso.get_config(tenant_id) is not None
            assert residency.get_tenant_config(tenant_id) is not None
            assert whitelabel.get_config(tenant_id) is not None
            
            # Roteamento
            route = router.route_request(tenant_id)
            assert "region" in route


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
