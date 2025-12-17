"""
Testes para Billing System e Marketplace

Suite de testes completa para validar:
- Metering Service
- Pricing Engine
- Plan Manager
- Billing Manager
- Marketplace
- Publisher
- Search
"""

import pytest
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# =============================================================================
# BILLING TESTS
# =============================================================================

class TestBillingTypes:
    """Testes para tipos do billing."""
    
    def test_usage_type_enum(self):
        """Testa enum UsageType."""
        from billing.types import UsageType
        
        assert UsageType.TOKENS_INPUT.value == "tokens_input"
        assert UsageType.TOKENS_OUTPUT.value == "tokens_output"
        assert UsageType.API_CALLS.value == "api_calls"
        assert UsageType.STORAGE_MB.value == "storage_mb"
        assert UsageType.AGENT_EXECUTIONS.value == "agent_executions"
        assert UsageType.WORKFLOW_RUNS.value == "workflow_runs"
    
    def test_invoice_status_enum(self):
        """Testa enum InvoiceStatus."""
        from billing.types import InvoiceStatus
        
        assert InvoiceStatus.DRAFT.value == "draft"
        assert InvoiceStatus.PENDING.value == "pending"
        assert InvoiceStatus.PAID.value == "paid"
        assert InvoiceStatus.OVERDUE.value == "overdue"
    
    def test_payment_status_enum(self):
        """Testa enum PaymentStatus."""
        from billing.types import PaymentStatus
        
        assert PaymentStatus.PENDING.value == "pending"
        assert PaymentStatus.COMPLETED.value == "completed"
        assert PaymentStatus.FAILED.value == "failed"
        assert PaymentStatus.REFUNDED.value == "refunded"
    
    def test_usage_record_creation(self):
        """Testa criação de UsageRecord."""
        from billing.types import UsageRecord, UsageType
        
        record = UsageRecord(
            user_id="user-123",
            usage_type=UsageType.TOKENS_INPUT,
            quantity=1000,
            model="gpt-4o"
        )
        
        assert record.user_id == "user-123"
        assert record.usage_type == UsageType.TOKENS_INPUT
        assert record.quantity == 1000
        assert record.model == "gpt-4o"
        assert record.id is not None
    
    def test_usage_record_to_dict(self):
        """Testa serialização de UsageRecord."""
        from billing.types import UsageRecord, UsageType
        
        record = UsageRecord(
            user_id="user-123",
            usage_type=UsageType.API_CALLS,
            quantity=50
        )
        
        data = record.to_dict()
        assert "id" in data
        assert data["user_id"] == "user-123"
        assert data["usage_type"] == "api_calls"
        assert data["quantity"] == 50
    
    def test_plan_features_creation(self):
        """Testa criação de PlanFeatures."""
        from billing.types import PlanFeatures
        
        features = PlanFeatures(
            max_agents=10,
            max_workflows=20,
            max_api_calls_per_day=5000,
            custom_models=True
        )
        
        assert features.max_agents == 10
        assert features.max_workflows == 20
        assert features.custom_models is True
    
    def test_plan_creation(self):
        """Testa criação de Plan."""
        from billing.types import Plan, PlanFeatures
        
        plan = Plan(
            id="pro",
            name="Pro",
            description="Pro plan",
            price_monthly=2900,
            features=PlanFeatures(max_agents=20)
        )
        
        assert plan.id == "pro"
        assert plan.name == "Pro"
        assert plan.price_monthly == 2900
        assert plan.features.max_agents == 20
    
    def test_invoice_creation(self):
        """Testa criação de Invoice."""
        from billing.types import Invoice, InvoiceStatus
        
        invoice = Invoice(user_id="user-123")
        
        assert invoice.user_id == "user-123"
        assert invoice.status == InvoiceStatus.DRAFT
        assert invoice.total == 0
        assert invoice.id is not None
    
    def test_invoice_add_item(self):
        """Testa adição de item a Invoice."""
        from billing.types import Invoice, InvoiceItem
        
        invoice = Invoice(user_id="user-123")
        
        item = InvoiceItem(
            description="Test item",
            quantity=10,
            unit_price=5.0,
            total=50.0
        )
        
        invoice.add_item(item)
        
        assert len(invoice.items) == 1
        assert invoice.subtotal == 50.0
        assert invoice.total == 50.0


class TestMeteringService:
    """Testes para MeteringService."""
    
    def test_metering_service_creation(self):
        """Testa criação do MeteringService."""
        from billing.metering import MeteringService
        
        metering = MeteringService()
        assert metering is not None
        assert metering._buffer_size == 100
    
    def test_track_tokens(self):
        """Testa rastreamento de tokens."""
        from billing.metering import MeteringService
        
        metering = MeteringService()
        records = metering.track_tokens(
            user_id="user-123",
            input_tokens=500,
            output_tokens=200,
            model="gpt-4o-mini"
        )
        
        assert len(records) == 2
        assert records[0].quantity == 500
        assert records[1].quantity == 200
    
    def test_track_api_call(self):
        """Testa rastreamento de API call."""
        from billing.metering import MeteringService
        
        metering = MeteringService()
        record = metering.track_api_call(
            user_id="user-123",
            endpoint="/api/agents/run"
        )
        
        assert record.user_id == "user-123"
        assert record.endpoint == "/api/agents/run"
        assert record.quantity == 1
    
    def test_track_agent_execution(self):
        """Testa rastreamento de execução de agente."""
        from billing.metering import MeteringService
        
        metering = MeteringService()
        record = metering.track_agent_execution(
            user_id="user-123",
            agent_id="agent-456",
            execution_time_ms=1500
        )
        
        assert record.user_id == "user-123"
        assert record.agent_id == "agent-456"
        assert record.metadata["execution_time_ms"] == 1500
    
    def test_track_workflow_run(self):
        """Testa rastreamento de execução de workflow."""
        from billing.metering import MeteringService
        
        metering = MeteringService()
        record = metering.track_workflow_run(
            user_id="user-123",
            workflow_id="wf-789",
            nodes_executed=5
        )
        
        assert record.workflow_id == "wf-789"
        assert record.metadata["nodes_executed"] == 5
    
    def test_track_storage(self):
        """Testa rastreamento de storage."""
        from billing.metering import MeteringService
        
        metering = MeteringService()
        record = metering.track_storage(
            user_id="user-123",
            size_mb=100.5
        )
        
        assert record.quantity == 100.5
        assert record.total_cost > 0
    
    def test_track_rag_query(self):
        """Testa rastreamento de RAG query."""
        from billing.metering import MeteringService
        
        metering = MeteringService()
        record = metering.track_rag_query(
            user_id="user-123",
            chunks_retrieved=10
        )
        
        assert record.quantity == 1
        assert record.metadata["chunks_retrieved"] == 10
    
    def test_track_embeddings(self):
        """Testa rastreamento de embeddings."""
        from billing.metering import MeteringService
        
        metering = MeteringService()
        record = metering.track_embeddings(
            user_id="user-123",
            tokens=5000,
            model="text-embedding-3-small"
        )
        
        assert record.quantity == 5000
        assert record.model == "text-embedding-3-small"
    
    def test_flush(self):
        """Testa flush do buffer."""
        from billing.metering import MeteringService
        
        metering = MeteringService()
        metering.track_api_call("user-123", "/test")
        metering.track_api_call("user-123", "/test2")
        
        count = metering.flush()
        assert count >= 0
    
    def test_get_usage_summary(self):
        """Testa obtenção de resumo de uso."""
        from billing.metering import MeteringService
        
        metering = MeteringService()
        
        # Track some usage
        metering.track_tokens("user-123", input_tokens=1000, output_tokens=500)
        metering.track_api_call("user-123", "/test")
        metering.flush()
        
        now = datetime.now()
        summary = metering.get_usage_summary(
            user_id="user-123",
            period_start=now - timedelta(hours=1),
            period_end=now + timedelta(hours=1)
        )
        
        assert summary.user_id == "user-123"
        assert summary.tokens_input >= 0
    
    def test_get_records(self):
        """Testa obtenção de records individuais."""
        from billing.metering import MeteringService
        
        metering = MeteringService()
        metering.track_api_call("user-123", "/test")
        metering.flush()
        
        records = metering.get_records("user-123", limit=10)
        assert isinstance(records, list)


class TestPricingEngine:
    """Testes para PricingEngine."""
    
    def test_pricing_engine_creation(self):
        """Testa criação do PricingEngine."""
        from billing.pricing import PricingEngine
        
        pricing = PricingEngine()
        assert pricing is not None
        assert pricing._markup == 20.0
    
    def test_pricing_engine_custom_markup(self):
        """Testa PricingEngine com markup customizado."""
        from billing.pricing import PricingEngine
        
        pricing = PricingEngine(markup_percent=30.0)
        assert pricing._markup == 30.0
    
    def test_get_base_price(self):
        """Testa obtenção de preço base."""
        from billing.pricing import PricingEngine
        from billing.types import UsageType
        
        pricing = PricingEngine()
        price = pricing.get_base_price(UsageType.TOKENS_INPUT)
        
        assert price > 0
    
    def test_set_custom_price(self):
        """Testa definição de preço customizado."""
        from billing.pricing import PricingEngine
        from billing.types import UsageType
        
        pricing = PricingEngine()
        pricing.set_custom_price(UsageType.API_CALLS, 0.001)
        
        price = pricing.get_base_price(UsageType.API_CALLS)
        assert price == 0.001
    
    def test_get_volume_discount(self):
        """Testa cálculo de desconto por volume."""
        from billing.pricing import PricingEngine
        from billing.types import UsageType
        
        pricing = PricingEngine()
        
        # Small volume - no discount
        discount = pricing.get_volume_discount(UsageType.TOKENS_INPUT, 1000)
        assert discount == 0
        
        # Large volume - should have discount
        discount = pricing.get_volume_discount(UsageType.TOKENS_INPUT, 1000000)
        assert discount >= 5
    
    def test_calculate_cost(self):
        """Testa cálculo de custo."""
        from billing.pricing import PricingEngine
        from billing.types import UsageType
        
        pricing = PricingEngine()
        result = pricing.calculate_cost(
            usage_type=UsageType.TOKENS_INPUT,
            quantity=10000
        )
        
        assert "total" in result
        assert "base_cost" in result
        assert "markup" in result
        assert result["quantity"] == 10000
    
    def test_calculate_cost_with_model(self):
        """Testa cálculo de custo com modelo específico."""
        from billing.pricing import PricingEngine
        from billing.types import UsageType
        
        pricing = PricingEngine()
        result = pricing.calculate_cost(
            usage_type=UsageType.TOKENS_INPUT,
            quantity=10000,
            model="gpt-4o"
        )
        
        assert result["total"] > 0
    
    def test_estimate_monthly_cost(self):
        """Testa estimativa de custo mensal."""
        from billing.pricing import PricingEngine
        
        pricing = PricingEngine()
        estimate = pricing.estimate_monthly_cost(
            tokens_per_day=10000,
            api_calls_per_day=100,
            storage_mb=500,
            agents=5,
            workflows=3
        )
        
        assert "estimated_monthly_cost" in estimate
        assert "breakdown" in estimate
        assert estimate["estimated_monthly_cost"] >= 0


class TestPlanManager:
    """Testes para PlanManager."""
    
    def test_plan_manager_creation(self):
        """Testa criação do PlanManager."""
        from billing.plans import PlanManager
        
        manager = PlanManager()
        assert manager is not None
    
    def test_default_plans_loaded(self):
        """Testa que planos padrão foram carregados."""
        from billing.plans import PlanManager
        
        manager = PlanManager()
        
        free = manager.get_plan("free")
        pro = manager.get_plan("pro")
        team = manager.get_plan("team")
        enterprise = manager.get_plan("enterprise")
        
        assert free is not None
        assert pro is not None
        assert team is not None
        assert enterprise is not None
    
    def test_free_plan_details(self):
        """Testa detalhes do plano Free."""
        from billing.plans import PlanManager
        
        manager = PlanManager()
        free = manager.get_plan("free")
        
        assert free.price_monthly == 0
        assert free.features.max_agents == 3
        assert free.features.max_workflows == 5
    
    def test_pro_plan_details(self):
        """Testa detalhes do plano Pro."""
        from billing.plans import PlanManager
        
        manager = PlanManager()
        pro = manager.get_plan("pro")
        
        assert pro.price_monthly == 2900
        assert pro.features.max_agents == 20
        assert pro.features.custom_models is True
    
    def test_get_all_plans(self):
        """Testa listagem de todos os planos."""
        from billing.plans import PlanManager
        
        manager = PlanManager()
        plans = manager.get_all_plans()
        
        assert len(plans) >= 4
    
    def test_assign_plan(self):
        """Testa atribuição de plano a usuário."""
        from billing.plans import PlanManager
        
        manager = PlanManager()
        result = manager.assign_plan("user-123", "pro")
        
        assert result is True
    
    def test_get_user_plan(self):
        """Testa obtenção de plano do usuário."""
        from billing.plans import PlanManager
        
        manager = PlanManager()
        manager.assign_plan("user-123", "team")
        
        plan = manager.get_user_plan("user-123")
        assert plan.id == "team"
    
    def test_get_user_plan_default(self):
        """Testa plano padrão (Free) para usuário sem plano."""
        from billing.plans import PlanManager
        
        manager = PlanManager()
        plan = manager.get_user_plan("new-user")
        
        assert plan.id == "free"
    
    def test_check_limit_allowed(self):
        """Testa verificação de limite (dentro do limite)."""
        from billing.plans import PlanManager
        
        manager = PlanManager()
        manager.assign_plan("user-123", "pro")
        
        result = manager.check_limit("user-123", "max_agents", 5)
        
        assert result["allowed"] is True
        assert result["current"] == 5
    
    def test_check_limit_exceeded(self):
        """Testa verificação de limite (excedido)."""
        from billing.plans import PlanManager
        
        manager = PlanManager()
        manager.assign_plan("user-123", "free")
        
        result = manager.check_limit("user-123", "max_agents", 10)
        
        assert result["allowed"] is False
        assert result["upgrade_available"] is True
    
    def test_can_use_feature(self):
        """Testa verificação de feature."""
        from billing.plans import PlanManager
        
        manager = PlanManager()
        
        manager.assign_plan("user-free", "free")
        manager.assign_plan("user-pro", "pro")
        
        assert manager.can_use_feature("user-free", "custom_models") is False
        assert manager.can_use_feature("user-pro", "custom_models") is True
    
    def test_compare_plans(self):
        """Testa comparação de planos."""
        from billing.plans import PlanManager
        
        manager = PlanManager()
        comparison = manager.compare_plans("free", "pro")
        
        assert "plans" in comparison
        assert "price_difference_monthly" in comparison
        assert comparison["price_difference_monthly"] == 2900
    
    def test_get_upgrade_options(self):
        """Testa opções de upgrade."""
        from billing.plans import PlanManager
        
        manager = PlanManager()
        manager.assign_plan("user-123", "free")
        
        upgrades = manager.get_upgrade_options("user-123")
        
        assert len(upgrades) >= 3
        assert upgrades[0].id == "pro"
    
    def test_calculate_proration(self):
        """Testa cálculo de proration."""
        from billing.plans import PlanManager
        
        manager = PlanManager()
        manager.assign_plan("user-123", "free")
        
        proration = manager.calculate_proration("user-123", "pro", days_remaining=15)
        
        assert "proration_amount" in proration
        assert proration["is_upgrade"] is True


class TestBillingManager:
    """Testes para BillingManager."""
    
    def test_billing_manager_creation(self):
        """Testa criação do BillingManager."""
        from billing.billing import BillingManager
        
        billing = BillingManager()
        assert billing is not None
    
    def test_generate_invoice(self):
        """Testa geração de fatura."""
        from billing.billing import BillingManager
        
        billing = BillingManager()
        invoice = billing.generate_invoice("user-123")
        
        assert invoice is not None
        assert invoice.user_id == "user-123"
        assert invoice.id is not None
    
    def test_generate_invoice_with_subscription(self):
        """Testa geração de fatura com assinatura."""
        from billing.billing import BillingManager
        from billing.plans import PlanManager
        
        plans = PlanManager()
        plans.assign_plan("user-456", "pro")
        
        billing = BillingManager(plans=plans)
        invoice = billing.generate_invoice("user-456", include_subscription=True)
        
        assert invoice.subtotal > 0
    
    def test_get_invoice(self):
        """Testa obtenção de fatura."""
        from billing.billing import BillingManager
        
        billing = BillingManager()
        created = billing.generate_invoice("user-123")
        
        retrieved = billing.get_invoice(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id
    
    def test_get_user_invoices(self):
        """Testa listagem de faturas do usuário."""
        from billing.billing import BillingManager
        
        billing = BillingManager()
        billing.generate_invoice("user-123")
        billing.generate_invoice("user-123")
        
        invoices = billing.get_user_invoices("user-123")
        assert len(invoices) >= 2
    
    def test_apply_discount(self):
        """Testa aplicação de desconto."""
        from billing.billing import BillingManager
        from billing.types import InvoiceStatus
        
        billing = BillingManager()
        invoice = billing.generate_invoice("user-123")
        invoice.status = InvoiceStatus.PENDING
        invoice.subtotal = 100
        invoice.total = 100
        
        updated = billing.apply_discount(invoice.id, 20, "Promo code")
        
        assert updated is not None
        assert updated.discount == 20
        assert updated.total == 80
    
    def test_process_payment(self):
        """Testa processamento de pagamento."""
        from billing.billing import BillingManager
        from billing.types import InvoiceStatus, PaymentStatus
        
        billing = BillingManager()
        invoice = billing.generate_invoice("user-123")
        invoice.status = InvoiceStatus.PENDING
        invoice.total = 29.00
        
        payment = billing.process_payment(invoice.id, "stripe")
        
        assert payment is not None
        assert payment.status == PaymentStatus.COMPLETED
        
        # Invoice should be paid
        updated_invoice = billing.get_invoice(invoice.id)
        assert updated_invoice.status == InvoiceStatus.PAID
    
    def test_get_billing_summary(self):
        """Testa resumo de billing."""
        from billing.billing import BillingManager
        
        billing = BillingManager()
        billing.generate_invoice("user-123")
        
        summary = billing.get_billing_summary("user-123", months=3)
        
        assert "user_id" in summary
        assert "total_spent" in summary
        assert "monthly_breakdown" in summary
    
    def test_check_payment_status(self):
        """Testa verificação de status de pagamento."""
        from billing.billing import BillingManager
        
        billing = BillingManager()
        
        status = billing.check_payment_status("user-123")
        
        assert "has_pending" in status
        assert "has_overdue" in status
        assert "account_status" in status


# =============================================================================
# MARKETPLACE TESTS
# =============================================================================

class TestMarketplaceTypes:
    """Testes para tipos do marketplace."""
    
    def test_listing_type_enum(self):
        """Testa enum ListingType."""
        from marketplace.types import ListingType
        
        assert ListingType.AGENT.value == "agent"
        assert ListingType.WORKFLOW.value == "workflow"
        assert ListingType.TEMPLATE.value == "template"
        assert ListingType.INTEGRATION.value == "integration"
        assert ListingType.TOOL.value == "tool"
    
    def test_listing_status_enum(self):
        """Testa enum ListingStatus."""
        from marketplace.types import ListingStatus
        
        assert ListingStatus.DRAFT.value == "draft"
        assert ListingStatus.PUBLISHED.value == "published"
        assert ListingStatus.SUSPENDED.value == "suspended"
    
    def test_listing_category_enum(self):
        """Testa enum ListingCategory."""
        from marketplace.types import ListingCategory
        
        assert ListingCategory.PRODUCTIVITY.value == "productivity"
        assert ListingCategory.CUSTOMER_SERVICE.value == "customer_service"
        assert ListingCategory.SALES.value == "sales"
    
    def test_listing_creation(self):
        """Testa criação de Listing."""
        from marketplace.types import Listing, ListingType, ListingCategory
        
        listing = Listing(
            name="Test Agent",
            description="A test agent for testing",
            type=ListingType.AGENT,
            category=ListingCategory.PRODUCTIVITY,
            author_id="author-123",
            author_name="Test Author"
        )
        
        assert listing.name == "Test Agent"
        assert listing.type == ListingType.AGENT
        assert listing.slug == "test-agent"
        assert listing.is_free is True
    
    def test_listing_with_price(self):
        """Testa Listing com preço."""
        from marketplace.types import Listing, ListingType, ListingCategory
        
        listing = Listing(
            name="Premium Agent",
            description="A premium agent",
            type=ListingType.AGENT,
            category=ListingCategory.SALES,
            price=2999,
            author_id="author-123",
            author_name="Test Author"
        )
        
        assert listing.price == 2999
        assert listing.is_free is False
    
    def test_listing_to_dict(self):
        """Testa serialização de Listing."""
        from marketplace.types import Listing, ListingType, ListingCategory
        
        listing = Listing(
            name="Test",
            description="Test description",
            type=ListingType.TOOL,
            category=ListingCategory.DEVELOPMENT,
            author_id="author-123",
            author_name="Author"
        )
        
        data = listing.to_dict()
        assert "id" in data
        assert data["name"] == "Test"
        assert data["type"] == "tool"
    
    def test_listing_to_summary(self):
        """Testa resumo de Listing."""
        from marketplace.types import Listing, ListingType, ListingCategory
        
        listing = Listing(
            name="Test",
            description="Full description",
            short_description="Short",
            type=ListingType.AGENT,
            category=ListingCategory.PRODUCTIVITY,
            author_id="author-123",
            author_name="Author"
        )
        
        summary = listing.to_summary()
        assert "short_description" in summary
        assert "description" not in summary
    
    def test_listing_version_creation(self):
        """Testa criação de ListingVersion."""
        from marketplace.types import ListingVersion
        
        version = ListingVersion(
            version="2.0.0",
            changelog="Major update with new features"
        )
        
        assert version.version == "2.0.0"
        assert version.changelog == "Major update with new features"
    
    def test_listing_add_version(self):
        """Testa adição de versão a Listing."""
        from marketplace.types import Listing, ListingVersion, ListingType, ListingCategory
        
        listing = Listing(
            name="Test",
            description="Test",
            type=ListingType.AGENT,
            category=ListingCategory.PRODUCTIVITY,
            author_id="author-123",
            author_name="Author"
        )
        
        version = ListingVersion(version="1.1.0", changelog="Bug fixes")
        listing.add_version(version)
        
        assert listing.current_version == "1.1.0"
        assert len(listing.versions) == 1
    
    def test_review_creation(self):
        """Testa criação de Review."""
        from marketplace.types import Review
        
        review = Review(
            listing_id="listing-123",
            user_id="user-456",
            user_name="John Doe",
            rating=5,
            title="Great agent!",
            content="This agent is amazing."
        )
        
        assert review.rating == 5
        assert review.is_verified_purchase is False
    
    def test_installation_creation(self):
        """Testa criação de Installation."""
        from marketplace.types import Installation
        
        installation = Installation(
            listing_id="listing-123",
            user_id="user-456",
            version="1.0.0"
        )
        
        assert installation.is_active is True
        assert installation.version == "1.0.0"


class TestMarketplace:
    """Testes para Marketplace."""
    
    def test_marketplace_creation(self):
        """Testa criação do Marketplace."""
        from marketplace.marketplace import Marketplace
        
        mp = Marketplace()
        assert mp is not None
    
    def test_sample_listings_loaded(self):
        """Testa que listings de exemplo foram carregados."""
        from marketplace.marketplace import Marketplace
        
        mp = Marketplace()
        
        listing = mp.get_listing("cs-agent-001")
        assert listing is not None
        assert listing.name == "Customer Support Agent"
    
    def test_get_listing_by_slug(self):
        """Testa obtenção por slug."""
        from marketplace.marketplace import Marketplace
        
        mp = Marketplace()
        
        listing = mp.get_listing_by_slug("customer-support-agent")
        assert listing is not None
    
    def test_list_all(self):
        """Testa listagem de todos os itens."""
        from marketplace.marketplace import Marketplace
        
        mp = Marketplace()
        listings = mp.list_all()
        
        assert len(listings) > 0
    
    def test_list_all_by_type(self):
        """Testa listagem filtrada por tipo."""
        from marketplace.marketplace import Marketplace
        from marketplace.types import ListingType
        
        mp = Marketplace()
        agents = mp.list_all(type=ListingType.AGENT)
        
        for listing in agents:
            assert listing.type == ListingType.AGENT
    
    def test_list_all_by_category(self):
        """Testa listagem filtrada por categoria."""
        from marketplace.marketplace import Marketplace
        from marketplace.types import ListingCategory
        
        mp = Marketplace()
        productivity = mp.list_all(category=ListingCategory.PRODUCTIVITY)
        
        for listing in productivity:
            assert listing.category == ListingCategory.PRODUCTIVITY
    
    def test_list_all_free_only(self):
        """Testa listagem apenas de gratuitos."""
        from marketplace.marketplace import Marketplace
        
        mp = Marketplace()
        free = mp.list_all(is_free=True)
        
        for listing in free:
            assert listing.is_free is True
    
    def test_get_featured(self):
        """Testa obtenção de itens em destaque."""
        from marketplace.marketplace import Marketplace
        
        mp = Marketplace()
        featured = mp.get_featured()
        
        for listing in featured:
            assert listing.is_featured is True
    
    def test_get_popular(self):
        """Testa obtenção de itens populares."""
        from marketplace.marketplace import Marketplace
        
        mp = Marketplace()
        popular = mp.get_popular(limit=5)
        
        assert len(popular) <= 5
        # Should be sorted by downloads
        for i in range(len(popular) - 1):
            assert popular[i].downloads >= popular[i + 1].downloads
    
    def test_get_top_rated(self):
        """Testa obtenção de itens melhor avaliados."""
        from marketplace.marketplace import Marketplace
        
        mp = Marketplace()
        top_rated = mp.get_top_rated(limit=5)
        
        assert len(top_rated) <= 5
    
    def test_get_categories(self):
        """Testa obtenção de contagem por categoria."""
        from marketplace.marketplace import Marketplace
        
        mp = Marketplace()
        categories = mp.get_categories()
        
        assert isinstance(categories, dict)
        assert len(categories) > 0
    
    def test_install(self):
        """Testa instalação de listing."""
        from marketplace.marketplace import Marketplace
        
        mp = Marketplace()
        
        installation = mp.install("cs-agent-001", "user-123")
        
        assert installation is not None
        assert installation.listing_id == "cs-agent-001"
        assert installation.user_id == "user-123"
    
    def test_install_already_installed(self):
        """Testa instalação duplicada (deve retornar existente)."""
        from marketplace.marketplace import Marketplace
        
        mp = Marketplace()
        
        inst1 = mp.install("cs-agent-001", "user-123")
        inst2 = mp.install("cs-agent-001", "user-123")
        
        assert inst1.id == inst2.id
    
    def test_uninstall(self):
        """Testa desinstalação."""
        from marketplace.marketplace import Marketplace
        
        mp = Marketplace()
        
        mp.install("rag-qa-001", "user-123")
        result = mp.uninstall("rag-qa-001", "user-123")
        
        assert result is True
        assert mp.is_installed("rag-qa-001", "user-123") is False
    
    def test_get_user_installations(self):
        """Testa obtenção de instalações do usuário."""
        from marketplace.marketplace import Marketplace
        
        mp = Marketplace()
        
        mp.install("cs-agent-001", "user-789")
        mp.install("slack-int-001", "user-789")
        
        installations = mp.get_user_installations("user-789")
        
        assert len(installations) >= 2
    
    def test_is_installed(self):
        """Testa verificação se está instalado."""
        from marketplace.marketplace import Marketplace
        
        mp = Marketplace()
        
        mp.install("cs-agent-001", "user-456")
        
        assert mp.is_installed("cs-agent-001", "user-456") is True
        assert mp.is_installed("cs-agent-001", "other-user") is False
    
    def test_add_review(self):
        """Testa adição de review."""
        from marketplace.marketplace import Marketplace
        
        mp = Marketplace()
        
        review = mp.add_review(
            listing_id="cs-agent-001",
            user_id="user-123",
            user_name="John Doe",
            rating=5,
            title="Excellent!",
            content="Works perfectly."
        )
        
        assert review is not None
        assert review.rating == 5
    
    def test_get_reviews(self):
        """Testa obtenção de reviews."""
        from marketplace.marketplace import Marketplace
        
        mp = Marketplace()
        
        mp.add_review("cs-agent-001", "user-1", "User 1", 5, "Great", "Great agent")
        mp.add_review("cs-agent-001", "user-2", "User 2", 4, "Good", "Good agent")
        
        reviews = mp.get_reviews("cs-agent-001")
        
        assert len(reviews) >= 2
    
    def test_get_stats(self):
        """Testa obtenção de estatísticas."""
        from marketplace.marketplace import Marketplace
        
        mp = Marketplace()
        stats = mp.get_stats()
        
        assert "total_listings" in stats
        assert "total_downloads" in stats
        assert "by_type" in stats


class TestPublisher:
    """Testes para Publisher."""
    
    def test_publisher_creation(self):
        """Testa criação do Publisher."""
        from marketplace.publisher import Publisher
        
        publisher = Publisher()
        assert publisher is not None
    
    def test_create_listing(self):
        """Testa criação de listing."""
        from marketplace.publisher import Publisher
        from marketplace.types import ListingType, ListingCategory, ListingStatus
        
        publisher = Publisher()
        
        listing = publisher.create_listing(
            author_id="author-123",
            author_name="Test Author",
            name="My New Agent",
            description="This is a test agent with many features",
            type=ListingType.AGENT,
            category=ListingCategory.PRODUCTIVITY,
            tags=["test", "automation"]
        )
        
        assert listing is not None
        assert listing.name == "My New Agent"
        assert listing.status == ListingStatus.DRAFT
    
    def test_update_listing(self):
        """Testa atualização de listing."""
        from marketplace.publisher import Publisher
        from marketplace.types import ListingType, ListingCategory
        
        publisher = Publisher()
        
        listing = publisher.create_listing(
            author_id="author-123",
            author_name="Author",
            name="Original Name",
            description="Original description that is long enough",
            type=ListingType.AGENT,
            category=ListingCategory.PRODUCTIVITY
        )
        
        updated = publisher.update_listing(
            listing.id,
            "author-123",
            name="Updated Name",
            description="Updated description"
        )
        
        assert updated is not None
        assert updated.name == "Updated Name"
    
    def test_update_listing_wrong_author(self):
        """Testa que atualização falha com autor errado."""
        from marketplace.publisher import Publisher
        from marketplace.types import ListingType, ListingCategory
        
        publisher = Publisher()
        
        listing = publisher.create_listing(
            author_id="author-123",
            author_name="Author",
            name="Test",
            description="Test description long enough",
            type=ListingType.AGENT,
            category=ListingCategory.PRODUCTIVITY
        )
        
        updated = publisher.update_listing(
            listing.id,
            "wrong-author",
            name="Hacked!"
        )
        
        assert updated is None
    
    def test_add_version(self):
        """Testa adição de versão."""
        from marketplace.publisher import Publisher
        from marketplace.types import ListingType, ListingCategory
        
        publisher = Publisher()
        
        listing = publisher.create_listing(
            author_id="author-123",
            author_name="Author",
            name="Versioned Agent",
            description="Agent with versions long description",
            type=ListingType.AGENT,
            category=ListingCategory.PRODUCTIVITY
        )
        
        version = publisher.add_version(
            listing.id,
            "author-123",
            version="1.1.0",
            changelog="Added new features"
        )
        
        assert version is not None
        assert version.version == "1.1.0"
    
    def test_validate_listing_valid(self):
        """Testa validação de listing válido."""
        from marketplace.publisher import Publisher
        from marketplace.types import Listing, ListingType, ListingCategory, ListingVersion
        
        publisher = Publisher()
        
        listing = Listing(
            name="Valid Agent",
            description="This is a valid agent with a long enough description for validation",
            type=ListingType.AGENT,
            category=ListingCategory.PRODUCTIVITY,
            author_id="author-123",
            author_name="Author"
        )
        listing.add_version(ListingVersion(version="1.0.0", changelog="Initial"))
        
        result = publisher.validate_listing(listing)
        
        assert result["valid"] is True
        assert len(result["errors"]) == 0
    
    def test_validate_listing_invalid(self):
        """Testa validação de listing inválido."""
        from marketplace.publisher import Publisher
        from marketplace.types import Listing, ListingType, ListingCategory
        
        publisher = Publisher()
        
        listing = Listing(
            name="Ab",  # Too short
            description="Short",  # Too short
            type=ListingType.AGENT,
            category=ListingCategory.PRODUCTIVITY,
            author_id="author-123",
            author_name="Author"
        )
        
        result = publisher.validate_listing(listing)
        
        assert result["valid"] is False
        assert len(result["errors"]) > 0
    
    def test_get_author_listings(self):
        """Testa listagem de listings do autor."""
        from marketplace.publisher import Publisher
        from marketplace.types import ListingType, ListingCategory
        
        publisher = Publisher()
        
        publisher.create_listing(
            author_id="author-999",
            author_name="Author",
            name="Agent 1",
            description="First agent with long description",
            type=ListingType.AGENT,
            category=ListingCategory.PRODUCTIVITY
        )
        
        publisher.create_listing(
            author_id="author-999",
            author_name="Author",
            name="Agent 2",
            description="Second agent with long description",
            type=ListingType.AGENT,
            category=ListingCategory.PRODUCTIVITY
        )
        
        listings = publisher.get_author_listings("author-999")
        
        assert len(listings) >= 2
    
    def test_get_publisher_stats(self):
        """Testa estatísticas do publisher."""
        from marketplace.publisher import Publisher
        from marketplace.types import ListingType, ListingCategory
        
        publisher = Publisher()
        
        publisher.create_listing(
            author_id="author-888",
            author_name="Author",
            name="Stats Agent",
            description="Agent for stats testing long description",
            type=ListingType.AGENT,
            category=ListingCategory.PRODUCTIVITY
        )
        
        stats = publisher.get_publisher_stats("author-888")
        
        assert "total_listings" in stats
        assert "total_downloads" in stats
        assert "average_rating" in stats


class TestMarketplaceSearch:
    """Testes para MarketplaceSearch."""
    
    def test_search_creation(self):
        """Testa criação do MarketplaceSearch."""
        from marketplace.search import MarketplaceSearch
        
        search = MarketplaceSearch()
        assert search is not None
    
    def test_search_basic(self):
        """Testa busca básica."""
        from marketplace.search import MarketplaceSearch
        
        search = MarketplaceSearch()
        results = search.search("support")
        
        assert "results" in results
        assert "total" in results
        assert len(results["results"]) > 0
    
    def test_search_empty_query(self):
        """Testa busca com query vazia."""
        from marketplace.search import MarketplaceSearch
        
        search = MarketplaceSearch()
        results = search.search("")
        
        assert "results" in results
        assert len(results["results"]) > 0
    
    def test_search_with_type_filter(self):
        """Testa busca com filtro de tipo."""
        from marketplace.search import MarketplaceSearch
        from marketplace.types import ListingType
        
        search = MarketplaceSearch()
        results = search.search("", type=ListingType.AGENT)
        
        for result in results["results"]:
            assert result["type"] == "agent"
    
    def test_search_with_category_filter(self):
        """Testa busca com filtro de categoria."""
        from marketplace.search import MarketplaceSearch
        from marketplace.types import ListingCategory
        
        search = MarketplaceSearch()
        results = search.search("", category=ListingCategory.PRODUCTIVITY)
        
        for result in results["results"]:
            assert result["category"] == "productivity"
    
    def test_search_free_only(self):
        """Testa busca apenas de gratuitos."""
        from marketplace.search import MarketplaceSearch
        
        search = MarketplaceSearch()
        results = search.search("", is_free=True)
        
        for result in results["results"]:
            assert result["is_free"] is True
    
    def test_search_with_min_rating(self):
        """Testa busca com rating mínimo."""
        from marketplace.search import MarketplaceSearch
        
        search = MarketplaceSearch()
        results = search.search("", min_rating=4.5)
        
        for result in results["results"]:
            assert result["rating"] >= 4.5
    
    def test_search_sort_by_downloads(self):
        """Testa busca ordenada por downloads."""
        from marketplace.search import MarketplaceSearch
        
        search = MarketplaceSearch()
        results = search.search("", sort_by="downloads")
        
        downloads = [r["downloads"] for r in results["results"]]
        assert downloads == sorted(downloads, reverse=True)
    
    def test_search_pagination(self):
        """Testa paginação da busca."""
        from marketplace.search import MarketplaceSearch
        
        search = MarketplaceSearch()
        
        page1 = search.search("", limit=2, offset=0)
        page2 = search.search("", limit=2, offset=2)
        
        if len(page1["results"]) >= 2 and len(page2["results"]) > 0:
            assert page1["results"][0]["id"] != page2["results"][0]["id"]
    
    def test_suggest(self):
        """Testa sugestões de busca."""
        from marketplace.search import MarketplaceSearch
        
        search = MarketplaceSearch()
        suggestions = search.suggest("supp")
        
        assert isinstance(suggestions, list)
    
    def test_get_trending(self):
        """Testa obtenção de trending."""
        from marketplace.search import MarketplaceSearch
        
        search = MarketplaceSearch()
        trending = search.get_trending(limit=5)
        
        assert len(trending) <= 5
    
    def test_get_related(self):
        """Testa obtenção de itens relacionados."""
        from marketplace.search import MarketplaceSearch
        
        search = MarketplaceSearch()
        related = search.get_related("cs-agent-001", limit=3)
        
        assert isinstance(related, list)
        # Should not include the original listing
        for listing in related:
            assert listing.id != "cs-agent-001"
    
    def test_get_filters(self):
        """Testa obtenção de opções de filtros."""
        from marketplace.search import MarketplaceSearch
        
        search = MarketplaceSearch()
        filters = search.get_filters()
        
        assert "types" in filters
        assert "categories" in filters
        assert "tags" in filters
        assert "price_ranges" in filters


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestBillingMarketplaceIntegration:
    """Testes de integração entre Billing e Marketplace."""
    
    def test_paid_listing_purchase_flow(self):
        """Testa fluxo de compra de listing pago."""
        from marketplace.marketplace import Marketplace
        from billing.billing import BillingManager
        from billing.types import InvoiceItem, InvoiceStatus
        
        mp = Marketplace()
        billing = BillingManager()
        
        # Get paid listing
        listing = mp.get_listing("sales-agent-001")
        assert listing is not None
        assert listing.price > 0
        
        # Create invoice for purchase
        invoice = billing.generate_invoice(
            "user-123",
            include_subscription=False,
            include_usage=False
        )
        
        # Add listing purchase item
        item = InvoiceItem(
            description=f"Marketplace: {listing.name}",
            quantity=1,
            unit_price=listing.price / 100,
            total=listing.price / 100
        )
        invoice.add_item(item)
        invoice.status = InvoiceStatus.PENDING
        
        # Process payment
        payment = billing.process_payment(invoice.id, "stripe")
        
        # Install after payment
        installation = mp.install(listing.id, "user-123")
        
        assert invoice.status == InvoiceStatus.PAID
        assert installation is not None
    
    def test_plan_limits_on_installations(self):
        """Testa limites de plano em instalações."""
        from marketplace.marketplace import Marketplace
        from billing.plans import PlanManager
        
        mp = Marketplace()
        plans = PlanManager()
        
        # User on free plan
        plans.assign_plan("user-limited", "free")
        
        # Check limit before install
        limit_check = plans.check_limit("user-limited", "max_agents", 2)
        assert limit_check["allowed"] is True
        
        # Install an agent
        mp.install("cs-agent-001", "user-limited")
        
        # Check limit after
        limit_check = plans.check_limit("user-limited", "max_agents", 3)
        assert limit_check["allowed"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
