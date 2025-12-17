"""
Billing Manager - Gerenciamento de Faturas e Pagamentos

Gerencia ciclo de billing completo.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import uuid

from .types import (
    Invoice, InvoiceItem, InvoiceStatus,
    Payment, PaymentStatus, UsageType
)
from .metering import MeteringService, get_metering_service
from .pricing import PricingEngine, get_pricing_engine
from .plans import PlanManager, get_plan_manager


class BillingManager:
    """
    Gerenciador de billing completo.
    
    Features:
    - Geração de faturas
    - Processamento de pagamentos
    - Histórico de transações
    - Webhooks para eventos
    """
    
    def __init__(
        self,
        metering: Optional[MeteringService] = None,
        pricing: Optional[PricingEngine] = None,
        plans: Optional[PlanManager] = None
    ):
        """
        Args:
            metering: Serviço de metering
            pricing: Motor de pricing
            plans: Gerenciador de planos
        """
        self._metering = metering or get_metering_service()
        self._pricing = pricing or get_pricing_engine()
        self._plans = plans or get_plan_manager()
        
        # Storage (in-memory para demo)
        self._invoices: Dict[str, Invoice] = {}
        self._payments: Dict[str, Payment] = {}
        self._user_invoices: Dict[str, List[str]] = {}  # user_id -> [invoice_ids]
    
    def generate_invoice(
        self,
        user_id: str,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
        include_subscription: bool = True,
        include_usage: bool = True,
        tenant_id: Optional[str] = None
    ) -> Invoice:
        """
        Gera fatura para um período.
        
        Args:
            user_id: ID do usuário
            period_start: Início do período (default: início do mês)
            period_end: Fim do período (default: fim do mês)
            include_subscription: Incluir cobrança de assinatura
            include_usage: Incluir cobrança de uso
            tenant_id: ID do tenant
            
        Returns:
            Invoice gerada
        """
        # Definir período
        now = datetime.now()
        if not period_start:
            period_start = datetime(now.year, now.month, 1)
        if not period_end:
            if now.month == 12:
                period_end = datetime(now.year + 1, 1, 1)
            else:
                period_end = datetime(now.year, now.month + 1, 1)
        
        # Criar fatura
        invoice = Invoice(
            user_id=user_id,
            tenant_id=tenant_id,
            period_start=period_start,
            period_end=period_end,
            due_date=period_end + timedelta(days=15)
        )
        
        # Adicionar assinatura
        if include_subscription:
            plan = self._plans.get_user_plan(user_id)
            if plan.price_monthly > 0:
                item = InvoiceItem(
                    description=f"Subscription: {plan.name} Plan",
                    quantity=1,
                    unit_price=plan.price_monthly / 100,  # Converter centavos para dólares
                    total=plan.price_monthly / 100
                )
                invoice.add_item(item)
        
        # Adicionar uso
        if include_usage:
            usage_summary = self._metering.get_usage_summary(
                user_id, period_start, period_end, tenant_id
            )
            
            cost_details = self._pricing.calculate_summary_cost(usage_summary)
            
            # Adicionar itens de uso
            if cost_details.get("breakdown"):
                for usage_item in cost_details["breakdown"]:
                    if usage_item["total"] > 0:
                        item = InvoiceItem(
                            description=f"Usage: {usage_item['usage_type']}",
                            quantity=usage_item["quantity"],
                            unit_price=usage_item["base_price"],
                            total=usage_item["total"] / 100,  # Converter centavos
                            usage_type=UsageType(usage_item["usage_type"])
                        )
                        invoice.add_item(item)
        
        # Aplicar impostos (simplificado)
        invoice.tax = invoice.subtotal * 0  # Sem impostos por enquanto
        invoice.total = invoice.subtotal + invoice.tax - invoice.discount
        
        # Status baseado no total
        if invoice.total <= 0:
            invoice.status = InvoiceStatus.PAID
        else:
            invoice.status = InvoiceStatus.PENDING
        
        # Salvar
        self._invoices[invoice.id] = invoice
        if user_id not in self._user_invoices:
            self._user_invoices[user_id] = []
        self._user_invoices[user_id].append(invoice.id)
        
        return invoice
    
    def get_invoice(self, invoice_id: str) -> Optional[Invoice]:
        """Obtém fatura pelo ID."""
        return self._invoices.get(invoice_id)
    
    def get_user_invoices(
        self,
        user_id: str,
        status: Optional[InvoiceStatus] = None,
        limit: int = 10
    ) -> List[Invoice]:
        """
        Lista faturas de um usuário.
        
        Args:
            user_id: ID do usuário
            status: Filtrar por status
            limit: Número máximo de faturas
            
        Returns:
            Lista de faturas
        """
        invoice_ids = self._user_invoices.get(user_id, [])
        
        invoices = []
        for inv_id in reversed(invoice_ids):  # Mais recentes primeiro
            invoice = self._invoices.get(inv_id)
            if invoice:
                if status is None or invoice.status == status:
                    invoices.append(invoice)
                    if len(invoices) >= limit:
                        break
        
        return invoices
    
    def apply_discount(
        self,
        invoice_id: str,
        discount_amount: float,
        reason: str = ""
    ) -> Optional[Invoice]:
        """
        Aplica desconto a uma fatura.
        
        Args:
            invoice_id: ID da fatura
            discount_amount: Valor do desconto
            reason: Motivo do desconto
            
        Returns:
            Fatura atualizada
        """
        invoice = self._invoices.get(invoice_id)
        if not invoice or invoice.status != InvoiceStatus.PENDING:
            return None
        
        invoice.discount = discount_amount
        invoice.total = invoice.subtotal + invoice.tax - invoice.discount
        invoice.metadata["discount_reason"] = reason
        
        return invoice
    
    def process_payment(
        self,
        invoice_id: str,
        payment_method: str,
        payment_provider_id: Optional[str] = None
    ) -> Payment:
        """
        Processa pagamento de uma fatura.
        
        Args:
            invoice_id: ID da fatura
            payment_method: Método de pagamento (stripe, paypal, etc)
            payment_provider_id: ID no provider
            
        Returns:
            Payment criado
        """
        invoice = self._invoices.get(invoice_id)
        if not invoice:
            raise ValueError(f"Invoice {invoice_id} not found")
        
        if invoice.status == InvoiceStatus.PAID:
            raise ValueError(f"Invoice {invoice_id} already paid")
        
        # Criar payment
        payment = Payment(
            invoice_id=invoice_id,
            user_id=invoice.user_id,
            amount=invoice.total,
            currency=invoice.currency,
            payment_method=payment_method,
            payment_provider_id=payment_provider_id,
            status=PaymentStatus.PROCESSING
        )
        
        # Simular processamento (em produção, integrar com gateway)
        try:
            # Aqui integraria com Stripe, PayPal, etc
            payment.status = PaymentStatus.COMPLETED
            payment.completed_at = datetime.now()
            
            # Atualizar fatura
            invoice.status = InvoiceStatus.PAID
            invoice.paid_at = datetime.now()
            invoice.payment_id = payment.id
            
        except Exception as e:
            payment.status = PaymentStatus.FAILED
            payment.error_message = str(e)
        
        # Salvar payment
        self._payments[payment.id] = payment
        
        return payment
    
    def refund_payment(
        self,
        payment_id: str,
        amount: Optional[float] = None,
        reason: str = ""
    ) -> Payment:
        """
        Processa reembolso de um pagamento.
        
        Args:
            payment_id: ID do pagamento
            amount: Valor a reembolsar (default: total)
            reason: Motivo do reembolso
            
        Returns:
            Payment atualizado
        """
        payment = self._payments.get(payment_id)
        if not payment:
            raise ValueError(f"Payment {payment_id} not found")
        
        if payment.status != PaymentStatus.COMPLETED:
            raise ValueError(f"Payment {payment_id} cannot be refunded")
        
        refund_amount = amount or payment.amount
        
        # Simular reembolso
        payment.status = PaymentStatus.REFUNDED
        payment.metadata = {
            "refund_amount": refund_amount,
            "refund_reason": reason,
            "refunded_at": datetime.now().isoformat()
        }
        
        # Atualizar fatura se reembolso total
        if refund_amount >= payment.amount:
            invoice = self._invoices.get(payment.invoice_id)
            if invoice:
                invoice.status = InvoiceStatus.CANCELLED
        
        return payment
    
    def get_payment(self, payment_id: str) -> Optional[Payment]:
        """Obtém pagamento pelo ID."""
        return self._payments.get(payment_id)
    
    def get_billing_summary(
        self,
        user_id: str,
        months: int = 6
    ) -> Dict[str, Any]:
        """
        Obtém resumo de billing dos últimos meses.
        
        Args:
            user_id: ID do usuário
            months: Número de meses
            
        Returns:
            Resumo de billing
        """
        now = datetime.now()
        monthly_totals = []
        total_spent = 0
        
        for i in range(months):
            # Calcular mês
            month = now.month - i
            year = now.year
            while month <= 0:
                month += 12
                year -= 1
            
            # Buscar faturas do mês
            start = datetime(year, month, 1)
            if month == 12:
                end = datetime(year + 1, 1, 1)
            else:
                end = datetime(year, month + 1, 1)
            
            month_total = 0
            for invoice in self._invoices.values():
                if (invoice.user_id == user_id and
                    invoice.period_start >= start and
                    invoice.period_start < end):
                    month_total += invoice.total
            
            monthly_totals.append({
                "year": year,
                "month": month,
                "total": round(month_total, 2)
            })
            total_spent += month_total
        
        # Plano atual
        plan = self._plans.get_user_plan(user_id)
        
        return {
            "user_id": user_id,
            "current_plan": plan.name,
            "monthly_cost": plan.price_monthly / 100,
            "total_spent": round(total_spent, 2),
            "monthly_breakdown": list(reversed(monthly_totals)),
            "pending_invoices": len([
                i for i in self._invoices.values()
                if i.user_id == user_id and i.status == InvoiceStatus.PENDING
            ])
        }
    
    def check_payment_status(self, user_id: str) -> Dict[str, Any]:
        """
        Verifica status de pagamentos do usuário.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Status de pagamentos
        """
        pending = []
        overdue = []
        now = datetime.now()
        
        for invoice in self._invoices.values():
            if invoice.user_id != user_id:
                continue
            
            if invoice.status == InvoiceStatus.PENDING:
                if invoice.due_date and invoice.due_date < now:
                    overdue.append(invoice)
                else:
                    pending.append(invoice)
        
        total_pending = sum(i.total for i in pending)
        total_overdue = sum(i.total for i in overdue)
        
        return {
            "user_id": user_id,
            "has_pending": len(pending) > 0,
            "has_overdue": len(overdue) > 0,
            "pending_count": len(pending),
            "overdue_count": len(overdue),
            "total_pending": round(total_pending, 2),
            "total_overdue": round(total_overdue, 2),
            "account_status": "overdue" if overdue else ("pending" if pending else "current")
        }


# Singleton instance
_billing_manager: Optional[BillingManager] = None


def get_billing_manager() -> BillingManager:
    """Obtém instância singleton do BillingManager."""
    global _billing_manager
    if _billing_manager is None:
        _billing_manager = BillingManager()
    return _billing_manager
