"""
Configuration module for EdgeMind MEC orchestration system.

This module defines MEC site configurations, threshold settings,
and simulation parameters for the EdgeMind system.
"""

import os
from dataclasses import dataclass
from enum import Enum

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class PrivacyLevel(Enum):
    """Privacy levels for data processing."""

    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


@dataclass
class MECSiteConfig:
    """Configuration for a MEC site."""

    site_id: str
    name: str
    location: str
    latitude: float
    longitude: float
    max_cpu_cores: int
    max_gpu_cores: int
    max_memory_gb: int
    network_latency_ms: dict[str, float]  # latency to other MEC sites


@dataclass
class ThresholdConfig:
    """Threshold configuration for orchestration triggers."""

    latency_threshold_ms: int = 100
    cpu_threshold_percent: float = 80.0
    gpu_threshold_percent: float = 80.0
    queue_depth_threshold: int = 50
    network_latency_threshold_ms: int = 20
    memory_threshold_percent: float = 85.0


@dataclass
class SimulationConfig:
    """Configuration for simulation parameters."""

    metrics_update_interval_ms: int = 1000
    swarm_consensus_timeout_ms: int = 50
    cache_refresh_interval_minutes: int = 15
    failover_timeout_ms: int = 100
    auto_scaling_enabled: bool = True
    demo_mode: bool = True


class MECConfig:
    """Main configuration class for MEC orchestration system."""

    def __init__(self):
        self.thresholds = ThresholdConfig(
            latency_threshold_ms=int(os.getenv("LATENCY_THRESHOLD_MS", "100")),
            cpu_threshold_percent=float(os.getenv("CPU_THRESHOLD_PERCENT", "80.0")),
            gpu_threshold_percent=float(os.getenv("GPU_THRESHOLD_PERCENT", "80.0")),
            queue_depth_threshold=int(os.getenv("QUEUE_DEPTH_THRESHOLD", "50")),
            network_latency_threshold_ms=int(
                os.getenv("NETWORK_LATENCY_THRESHOLD_MS", "20"),
            ),
            memory_threshold_percent=float(
                os.getenv("MEMORY_THRESHOLD_PERCENT", "85.0"),
            ),
        )

        self.simulation = SimulationConfig(
            metrics_update_interval_ms=int(
                os.getenv("METRICS_UPDATE_INTERVAL_MS", "1000"),
            ),
            swarm_consensus_timeout_ms=int(
                os.getenv("SWARM_CONSENSUS_TIMEOUT_MS", "50"),
            ),
            cache_refresh_interval_minutes=int(
                os.getenv("CACHE_REFRESH_INTERVAL_MINUTES", "15"),
            ),
            failover_timeout_ms=int(os.getenv("FAILOVER_TIMEOUT_MS", "100")),
            auto_scaling_enabled=os.getenv("AUTO_SCALING_ENABLED", "true").lower()
            == "true",
            demo_mode=os.getenv("DEMO_MODE", "true").lower() == "true",
        )

        self.mec_sites = self._initialize_mec_sites()

    def _initialize_mec_sites(self) -> dict[str, MECSiteConfig]:
        """Initialize MEC site configurations."""
        return {
            "MEC_A": MECSiteConfig(
                site_id="MEC_A",
                name="MEC Site Alpha",
                location="New York, NY",
                latitude=40.7128,
                longitude=-74.0060,
                max_cpu_cores=32,
                max_gpu_cores=8,
                max_memory_gb=128,
                network_latency_ms={"MEC_B": 15.0, "MEC_C": 25.0},
            ),
            "MEC_B": MECSiteConfig(
                site_id="MEC_B",
                name="MEC Site Beta",
                location="Chicago, IL",
                latitude=41.8781,
                longitude=-87.6298,
                max_cpu_cores=24,
                max_gpu_cores=6,
                max_memory_gb=96,
                network_latency_ms={"MEC_A": 15.0, "MEC_C": 18.0},
            ),
            "MEC_C": MECSiteConfig(
                site_id="MEC_C",
                name="MEC Site Gamma",
                location="Los Angeles, CA",
                latitude=34.0522,
                longitude=-118.2437,
                max_cpu_cores=28,
                max_gpu_cores=7,
                max_memory_gb=112,
                network_latency_ms={"MEC_A": 25.0, "MEC_B": 18.0},
            ),
        }

    def get_mec_site(self, site_id: str) -> MECSiteConfig:
        """Get MEC site configuration by ID."""
        return self.mec_sites.get(site_id)

    def get_all_mec_sites(self) -> list[MECSiteConfig]:
        """Get all MEC site configurations."""
        return list(self.mec_sites.values())


# Global configuration instance
config = MECConfig()
