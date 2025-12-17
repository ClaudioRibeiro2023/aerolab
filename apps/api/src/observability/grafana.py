"""
Templates e configurações para Grafana.

Gera dashboards JSON para importação no Grafana.
"""

import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class GrafanaPanel:
    """Painel do dashboard."""
    title: str
    type: str  # graph, stat, gauge, table, heatmap
    targets: List[Dict[str, Any]]
    gridPos: Dict[str, int]
    options: Optional[Dict[str, Any]] = None


class GrafanaDashboardBuilder:
    """Builder para criar dashboards Grafana."""
    
    def __init__(
        self,
        title: str,
        uid: Optional[str] = None,
        tags: Optional[List[str]] = None
    ):
        self.title = title
        self.uid = uid or title.lower().replace(" ", "-")
        self.tags = tags or ["agentos", "monitoring"]
        self.panels: List[Dict[str, Any]] = []
        self._panel_id = 1
    
    def add_stat_panel(
        self,
        title: str,
        query: str,
        x: int = 0,
        y: int = 0,
        w: int = 6,
        h: int = 4,
        unit: str = "short"
    ) -> "GrafanaDashboardBuilder":
        """Adiciona painel de estatística."""
        self.panels.append({
            "id": self._panel_id,
            "type": "stat",
            "title": title,
            "gridPos": {"x": x, "y": y, "w": w, "h": h},
            "targets": [{"expr": query, "refId": "A"}],
            "fieldConfig": {
                "defaults": {"unit": unit}
            }
        })
        self._panel_id += 1
        return self
    
    def add_graph_panel(
        self,
        title: str,
        queries: List[Dict[str, str]],
        x: int = 0,
        y: int = 0,
        w: int = 12,
        h: int = 8
    ) -> "GrafanaDashboardBuilder":
        """Adiciona painel de gráfico."""
        targets = [
            {"expr": q["query"], "legendFormat": q.get("legend", ""), "refId": chr(65 + i)}
            for i, q in enumerate(queries)
        ]
        
        self.panels.append({
            "id": self._panel_id,
            "type": "timeseries",
            "title": title,
            "gridPos": {"x": x, "y": y, "w": w, "h": h},
            "targets": targets,
            "options": {
                "legend": {"displayMode": "table", "placement": "bottom"},
                "tooltip": {"mode": "multi"}
            }
        })
        self._panel_id += 1
        return self
    
    def add_gauge_panel(
        self,
        title: str,
        query: str,
        min_val: float = 0,
        max_val: float = 100,
        thresholds: Optional[List[Dict]] = None,
        x: int = 0,
        y: int = 0,
        w: int = 6,
        h: int = 6
    ) -> "GrafanaDashboardBuilder":
        """Adiciona painel gauge."""
        self.panels.append({
            "id": self._panel_id,
            "type": "gauge",
            "title": title,
            "gridPos": {"x": x, "y": y, "w": w, "h": h},
            "targets": [{"expr": query, "refId": "A"}],
            "fieldConfig": {
                "defaults": {
                    "min": min_val,
                    "max": max_val,
                    "thresholds": {
                        "mode": "absolute",
                        "steps": thresholds or [
                            {"color": "green", "value": None},
                            {"color": "yellow", "value": 70},
                            {"color": "red", "value": 90}
                        ]
                    }
                }
            }
        })
        self._panel_id += 1
        return self
    
    def add_table_panel(
        self,
        title: str,
        query: str,
        x: int = 0,
        y: int = 0,
        w: int = 24,
        h: int = 8
    ) -> "GrafanaDashboardBuilder":
        """Adiciona painel de tabela."""
        self.panels.append({
            "id": self._panel_id,
            "type": "table",
            "title": title,
            "gridPos": {"x": x, "y": y, "w": w, "h": h},
            "targets": [{"expr": query, "refId": "A", "format": "table"}],
            "options": {
                "showHeader": True,
                "sortBy": [{"displayName": "Value", "desc": True}]
            }
        })
        self._panel_id += 1
        return self
    
    def build(self) -> Dict[str, Any]:
        """Gera JSON do dashboard."""
        return {
            "dashboard": {
                "uid": self.uid,
                "title": self.title,
                "tags": self.tags,
                "timezone": "browser",
                "refresh": "30s",
                "time": {"from": "now-1h", "to": "now"},
                "panels": self.panels,
                "templating": {"list": []},
                "annotations": {"list": []},
                "schemaVersion": 38,
                "version": 1
            },
            "overwrite": True
        }
    
    def to_json(self, indent: int = 2) -> str:
        """Exporta para JSON."""
        return json.dumps(self.build(), indent=indent)


def create_agentos_dashboard() -> Dict[str, Any]:
    """Cria dashboard principal do AgentOS."""
    builder = GrafanaDashboardBuilder("AgentOS Overview", "agentos-main")
    
    # Row 1: Estatísticas principais
    builder.add_stat_panel(
        "Total Requests", 
        "sum(agentos_requests_total)",
        x=0, y=0, w=6, h=4
    )
    builder.add_stat_panel(
        "Active Agents",
        "agentos_active_agents",
        x=6, y=0, w=6, h=4
    )
    builder.add_stat_panel(
        "Avg Response Time",
        "avg(rate(agentos_request_duration_seconds_sum[5m]) / rate(agentos_request_duration_seconds_count[5m]))",
        x=12, y=0, w=6, h=4,
        unit="s"
    )
    builder.add_stat_panel(
        "Error Rate",
        "sum(rate(agentos_errors_total[5m])) / sum(rate(agentos_requests_total[5m])) * 100",
        x=18, y=0, w=6, h=4,
        unit="percent"
    )
    
    # Row 2: Gráficos de tráfego
    builder.add_graph_panel(
        "Requests Over Time",
        [
            {"query": "sum(rate(agentos_requests_total[5m]))", "legend": "Total"},
            {"query": "sum(rate(agentos_requests_total{status='2xx'}[5m]))", "legend": "Success"},
            {"query": "sum(rate(agentos_requests_total{status='5xx'}[5m]))", "legend": "Errors"}
        ],
        x=0, y=4, w=12, h=8
    )
    builder.add_graph_panel(
        "Response Time Distribution",
        [
            {"query": "histogram_quantile(0.50, rate(agentos_request_duration_seconds_bucket[5m]))", "legend": "p50"},
            {"query": "histogram_quantile(0.95, rate(agentos_request_duration_seconds_bucket[5m]))", "legend": "p95"},
            {"query": "histogram_quantile(0.99, rate(agentos_request_duration_seconds_bucket[5m]))", "legend": "p99"}
        ],
        x=12, y=4, w=12, h=8
    )
    
    # Row 3: Agentes
    builder.add_graph_panel(
        "Agent Executions",
        [
            {"query": "sum(rate(agentos_agent_executions_total[5m])) by (agent)", "legend": "{{agent}}"}
        ],
        x=0, y=12, w=12, h=8
    )
    builder.add_gauge_panel(
        "CPU Usage",
        "100 - (avg(rate(node_cpu_seconds_total{mode='idle'}[5m])) * 100)",
        x=12, y=12, w=6, h=6
    )
    builder.add_gauge_panel(
        "Memory Usage",
        "(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100",
        x=18, y=12, w=6, h=6
    )
    
    # Row 4: Tokens e Custos
    builder.add_graph_panel(
        "Token Usage",
        [
            {"query": "sum(rate(agentos_tokens_total[1h]))", "legend": "Total Tokens"}
        ],
        x=0, y=20, w=12, h=6
    )
    builder.add_table_panel(
        "Top Agents by Executions",
        "topk(10, sum(agentos_agent_executions_total) by (agent))",
        x=12, y=20, w=12, h=6
    )
    
    return builder.build()


def create_sla_dashboard() -> Dict[str, Any]:
    """Cria dashboard de SLA."""
    builder = GrafanaDashboardBuilder("AgentOS SLA", "agentos-sla", ["agentos", "sla"])
    
    # Uptime
    builder.add_stat_panel(
        "Uptime (30d)",
        "(1 - (sum(increase(agentos_errors_total[30d])) / sum(increase(agentos_requests_total[30d])))) * 100",
        x=0, y=0, w=8, h=5,
        unit="percent"
    )
    builder.add_stat_panel(
        "Avg Latency (24h)",
        "avg(rate(agentos_request_duration_seconds_sum[24h]) / rate(agentos_request_duration_seconds_count[24h]))",
        x=8, y=0, w=8, h=5,
        unit="s"
    )
    builder.add_stat_panel(
        "Incidents (7d)",
        "count(changes(agentos_errors_total[7d]) > 10)",
        x=16, y=0, w=8, h=5
    )
    
    # SLA Compliance
    builder.add_gauge_panel(
        "SLA Compliance",
        "(1 - (sum(rate(agentos_errors_total[24h])) / sum(rate(agentos_requests_total[24h])))) * 100",
        thresholds=[
            {"color": "red", "value": None},
            {"color": "yellow", "value": 99},
            {"color": "green", "value": 99.9}
        ],
        x=0, y=5, w=12, h=8
    )
    
    builder.add_graph_panel(
        "Error Budget Consumption",
        [
            {"query": "(1 - ((1 - (sum(rate(agentos_errors_total[1h])) / sum(rate(agentos_requests_total[1h])))) / 0.999)) * 100", "legend": "Budget Used %"}
        ],
        x=12, y=5, w=12, h=8
    )
    
    return builder.build()


def create_agents_dashboard() -> Dict[str, Any]:
    """Cria dashboard de agentes."""
    builder = GrafanaDashboardBuilder("AgentOS Agents", "agentos-agents", ["agentos", "agents"])
    
    builder.add_stat_panel(
        "Total Executions",
        "sum(agentos_agent_executions_total)",
        x=0, y=0, w=6, h=4
    )
    builder.add_stat_panel(
        "Unique Agents",
        "count(count by (agent)(agentos_agent_executions_total))",
        x=6, y=0, w=6, h=4
    )
    builder.add_stat_panel(
        "Avg Tokens/Execution",
        "sum(agentos_tokens_total) / sum(agentos_agent_executions_total)",
        x=12, y=0, w=6, h=4
    )
    builder.add_stat_panel(
        "Cache Hit Rate",
        "sum(agentos_cache_hits_total) / (sum(agentos_cache_hits_total) + sum(agentos_cache_misses_total)) * 100",
        x=18, y=0, w=6, h=4,
        unit="percent"
    )
    
    builder.add_graph_panel(
        "Executions by Agent",
        [{"query": "sum(rate(agentos_agent_executions_total[5m])) by (agent)", "legend": "{{agent}}"}],
        x=0, y=4, w=24, h=10
    )
    
    builder.add_table_panel(
        "Agent Performance",
        "sum by (agent)(agentos_agent_executions_total)",
        x=0, y=14, w=24, h=8
    )
    
    return builder.build()


def export_all_dashboards(output_dir: str = "./grafana"):
    """Exporta todos os dashboards para arquivos JSON."""
    import os
    from pathlib import Path
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    dashboards = {
        "agentos-overview.json": create_agentos_dashboard(),
        "agentos-sla.json": create_sla_dashboard(),
        "agentos-agents.json": create_agents_dashboard(),
    }
    
    for filename, dashboard in dashboards.items():
        filepath = output_path / filename
        filepath.write_text(json.dumps(dashboard, indent=2))
        print(f"✓ Exported: {filepath}")
    
    # Criar provisioning config
    provisioning = {
        "apiVersion": 1,
        "providers": [{
            "name": "AgentOS",
            "folder": "AgentOS",
            "type": "file",
            "disableDeletion": False,
            "editable": True,
            "options": {"path": "/var/lib/grafana/dashboards/agentos"}
        }]
    }
    
    prov_file = output_path / "provisioning.yml"
    import yaml
    try:
        prov_file.write_text(yaml.dump(provisioning, default_flow_style=False))
    except ImportError:
        prov_file.write_text(json.dumps(provisioning, indent=2))
    
    print(f"✓ Provisioning config: {prov_file}")
    return list(dashboards.keys())
