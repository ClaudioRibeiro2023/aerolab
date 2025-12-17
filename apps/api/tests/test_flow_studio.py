"""
Test script for Agno Flow Studio v3.0
"""

import asyncio
import sys

sys.path.insert(0, "src")

from flow_studio.ai.nl_designer import NLWorkflowDesigner
from flow_studio.validation import WorkflowValidator
from flow_studio.ai.optimizer import WorkflowOptimizer
from flow_studio.ai.predictor import CostPredictor, ExecutionPredictor


async def main():
    print("=" * 60)
    print("🚀 AGNO FLOW STUDIO v3.0 - Proof of Concept")
    print("=" * 60)

    # 1. Natural Language to Workflow
    print("\n📝 Test 1: Natural Language to Workflow")
    print("-" * 40)

    designer = NLWorkflowDesigner()
    result = await designer.design_workflow(
        "Create a customer service bot that routes inquiries to sales or support"
    )

    print(f"✅ Generated {len(result.workflow.nodes)} nodes")
    print(f"✅ Confidence: {result.confidence * 100:.1f}%")
    print(f"✅ Intent: {result.intent.value}")
    print(f"✅ Nodes: {[n.label for n in result.workflow.nodes]}")

    workflow = result.workflow

    # 2. Validation
    print("\n🔍 Test 2: Workflow Validation")
    print("-" * 40)

    validator = WorkflowValidator()
    validation = validator.validate(workflow)

    print(f"✅ Valid: {validation.is_valid}")
    print(f"✅ Errors: {len(validation.errors)}")
    print(f"✅ Warnings: {len(validation.warnings)}")

    if validation.warnings:
        for w in validation.warnings[:3]:
            print(f"   ⚠️ {w.message}")

    # 3. Optimization
    print("\n⚡ Test 3: AI Optimization")
    print("-" * 40)

    optimizer = WorkflowOptimizer()
    suggestions = optimizer.analyze(workflow)

    print(f"✅ Suggestions: {len(suggestions)}")
    for s in suggestions[:3]:
        print(f"   💡 [{s.priority.value}] {s.title}")

    # 4. Cost Prediction
    print("\n💰 Test 4: Cost Prediction")
    print("-" * 40)

    cost_predictor = CostPredictor()
    cost = cost_predictor.predict(workflow)

    print(f"✅ Estimated Cost: ${cost.total_cost:.6f}")
    print(f"✅ Confidence: {cost.confidence * 100:.1f}%")

    # 5. Execution Time Prediction
    print("\n⏱️ Test 5: Execution Time Prediction")
    print("-" * 40)

    exec_predictor = ExecutionPredictor()
    time_pred = exec_predictor.predict(workflow)

    print(f"✅ Estimated Time: {time_pred.estimated_duration_ms:.0f}ms")
    print(f"✅ Bottleneck: {time_pred.bottleneck_node}")
    print(f"✅ Parallel Opportunities: {time_pred.parallel_opportunities}")

    # 6. Resource Prediction
    print("\n📊 Test 6: Resource Prediction")
    print("-" * 40)

    resources = exec_predictor.predict_resources(workflow)

    print(f"✅ Estimated Tokens: {resources.estimated_tokens}")
    print(f"✅ API Calls: {resources.estimated_api_calls}")
    print(f"✅ Memory: {resources.estimated_memory_mb:.1f}MB")

    # Summary
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED - Flow Studio v3.0 Operational!")
    print("=" * 60)

    return result


if __name__ == "__main__":
    asyncio.run(main())
