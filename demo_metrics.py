#!/usr/bin/env python3
"""
Demo script showing MEC metrics generation and data persistence capabilities.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config import config
from data import DataStore, MECMetricsGenerator, OperationMode


def main():
    """Demonstrate key features of the metrics system."""
    print("🚀 EdgeMind MEC Metrics Demo")
    print("=" * 40)

    # Initialize components
    generator = MECMetricsGenerator(config)
    data_store = DataStore("demo_data")

    print("\n📊 Generating metrics for all MEC sites:")

    # Generate normal metrics
    for site_id in config.mec_sites:
        metrics = generator.generate_metrics(site_id)
        data_store.store_metrics(metrics)

        print(
            f"  {site_id}: CPU={metrics.cpu_utilization:.1f}%, "
            f"GPU={metrics.gpu_utilization:.1f}%, "
            f"Latency={metrics.response_time_ms:.1f}ms, "
            f"Queue={metrics.queue_depth}",
        )

    print("\n⚠️  Simulating threshold breach scenario:")

    # Trigger threshold breach
    generator.set_operation_mode(OperationMode.THRESHOLD_BREACH, "MEC_A")
    breach_metrics = generator.generate_metrics("MEC_A")
    data_store.store_metrics(breach_metrics)

    print(
        f"  MEC_A (breach): CPU={breach_metrics.cpu_utilization:.1f}%, "
        f"Latency={breach_metrics.response_time_ms:.1f}ms, "
        f"Queue={breach_metrics.queue_depth}",
    )

    # Check for breaches
    breach_summary = generator.get_breach_summary(breach_metrics)

    if breach_summary["has_breaches"]:
        print(f"  🔴 {breach_summary['total_breaches']} thresholds breached!")
        print(f"  📋 Breached metrics: {', '.join(breach_summary['breached_metrics'])}")

    print("\n� Data persistence features:")

    # Export data
    json_export = data_store.export_data("json", hours=1)
    csv_export = data_store.export_data("csv", hours=1)

    print(f"  📄 JSON export: {json_export}")
    print(f"  📊 CSV export: {csv_export}")

    # Storage stats
    stats = data_store.get_storage_stats()
    print(
        f"  💽 Storage: {stats['total_size_mb']} MB, {stats['total_metrics_records']} records",
    )

    print("\n✅ Demo completed successfully!")
    print("\nKey Features Demonstrated:")
    print("  • Realistic MEC metrics generation with variance")
    print("  • Configurable threshold breach scenarios")
    print("  • JSON-based data persistence")
    print("  • Session state management")
    print("  • Data export (JSON/CSV)")
    print("  • Threshold monitoring and breach detection")


if __name__ == "__main__":
    main()
