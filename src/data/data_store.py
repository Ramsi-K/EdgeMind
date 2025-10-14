"""
Data persistence layer for EdgeMind MEC orchestration system.

This module provides JSON-based data storage for metrics history,
session state management for Streamlit continuity, and data export
functionality for analysis.
"""

import csv
import json
import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

try:
    import streamlit as st
except ImportError:
    st = None

from .metrics_generator import MECMetrics


class DataStore:
    """
    JSON-based data store for MEC metrics and system state.

    Features:
    - Persistent storage of metrics history
    - Session state management for Streamlit
    - Data export functionality (CSV, JSON)
    - Automatic data cleanup and archiving
    - Thread-safe operations
    """

    def __init__(self, data_dir: str = "data", max_history_days: int = 7):
        """
        Initialize the data store.

        Args:
            data_dir: Directory for data storage
            max_history_days: Maximum days to keep historical data
        """
        self.data_dir = Path(data_dir)
        self.max_history_days = max_history_days

        # Create directory structure
        self.data_dir.mkdir(exist_ok=True)
        (self.data_dir / "metrics").mkdir(exist_ok=True)
        (self.data_dir / "sessions").mkdir(exist_ok=True)
        (self.data_dir / "exports").mkdir(exist_ok=True)
        (self.data_dir / "archive").mkdir(exist_ok=True)

        # File paths
        self.metrics_file = self.data_dir / "metrics" / "current_metrics.json"
        self.history_file = self.data_dir / "metrics" / "metrics_history.json"
        self.session_file = self.data_dir / "sessions" / "session_state.json"
        self.config_file = self.data_dir / "config.json"

        # Initialize files if they don't exist
        self._initialize_files()

    def _initialize_files(self) -> None:
        """Initialize data files with default structures."""
        if not self.metrics_file.exists():
            self._write_json(self.metrics_file, {})

        if not self.history_file.exists():
            self._write_json(self.history_file, {"metrics": [], "last_updated": None})

        if not self.session_file.exists():
            self._write_json(
                self.session_file,
                {
                    "session_id": None,
                    "created_at": None,
                    "last_accessed": None,
                    "state": {},
                },
            )

        if not self.config_file.exists():
            self._write_json(
                self.config_file,
                {
                    "version": "1.0",
                    "created_at": datetime.now(UTC).isoformat(),
                    "settings": {
                        "auto_cleanup_enabled": True,
                        "max_history_days": self.max_history_days,
                        "export_format": "json",
                    },
                },
            )

    def _read_json(self, file_path: Path) -> dict[str, Any]:
        """Safely read JSON file."""
        try:
            with file_path.open(encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _write_json(self, file_path: Path, data: dict[str, Any]) -> None:
        """Safely write JSON file."""
        # Write to temporary file first, then rename for atomicity
        temp_file = file_path.with_suffix(".tmp")
        try:
            with temp_file.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            temp_file.replace(file_path)
        except Exception:
            if temp_file.exists():
                temp_file.unlink()
            raise

    def store_metrics(self, metrics: MECMetrics) -> None:
        """
        Store current metrics for a MEC site.

        Args:
            metrics: MECMetrics object to store
        """
        current_data = self._read_json(self.metrics_file)

        # Store current metrics by site_id
        current_data[metrics.site_id] = metrics.to_dict()
        current_data["last_updated"] = datetime.now(UTC).isoformat()

        self._write_json(self.metrics_file, current_data)

        # Also add to history
        self._add_to_history(metrics)

    def store_metrics_batch(self, metrics_list: list[MECMetrics]) -> None:
        """
        Store multiple metrics efficiently.

        Args:
            metrics_list: List of MECMetrics objects to store
        """
        if not metrics_list:
            return

        current_data = self._read_json(self.metrics_file)

        # Update current metrics for all sites
        for metrics in metrics_list:
            current_data[metrics.site_id] = metrics.to_dict()

        current_data["last_updated"] = datetime.now(UTC).isoformat()
        self._write_json(self.metrics_file, current_data)

        # Add all to history
        for metrics in metrics_list:
            self._add_to_history(metrics)

    def _add_to_history(self, metrics: MECMetrics) -> None:
        """Add metrics to historical data."""
        history_data = self._read_json(self.history_file)

        if "metrics" not in history_data:
            history_data["metrics"] = []

        history_data["metrics"].append(metrics.to_dict())
        history_data["last_updated"] = datetime.now(UTC).isoformat()

        # Keep only recent history to prevent file from growing too large
        self._cleanup_old_history(history_data)

        self._write_json(self.history_file, history_data)

    def _cleanup_old_history(self, history_data: dict[str, Any]) -> None:
        """Remove old historical data beyond retention period."""
        if "metrics" not in history_data:
            return

        cutoff_date = datetime.now(UTC) - timedelta(days=self.max_history_days)

        # Filter out old metrics
        filtered_metrics = []
        for metric_data in history_data["metrics"]:
            try:
                metric_time = datetime.fromisoformat(metric_data["timestamp"])
                if metric_time > cutoff_date:
                    filtered_metrics.append(metric_data)
            except (KeyError, ValueError):
                # Keep metrics with invalid timestamps for safety
                filtered_metrics.append(metric_data)

        history_data["metrics"] = filtered_metrics

    def get_current_metrics(
        self,
        site_id: str | None = None,
    ) -> dict[str, Any] | MECMetrics | None:
        """
        Get current metrics for a site or all sites.

        Args:
            site_id: Specific site ID, or None for all sites

        Returns:
            MECMetrics object for specific site, or dict of all sites
        """
        current_data = self._read_json(self.metrics_file)

        if site_id:
            if site_id in current_data and isinstance(current_data[site_id], dict):
                return MECMetrics.from_dict(current_data[site_id])
            return None

        # Return all current metrics (excluding metadata)
        return {
            k: v
            for k, v in current_data.items()
            if k not in ["last_updated"] and isinstance(v, dict)
        }

    def get_metrics_history(
        self,
        site_id: str | None = None,
        hours: int = 24,
        limit: int | None = None,
    ) -> list[MECMetrics]:
        """
        Get historical metrics for analysis.

        Args:
            site_id: Specific site ID, or None for all sites
            hours: Number of hours of history to retrieve
            limit: Maximum number of records to return

        Returns:
            List of MECMetrics objects
        """
        history_data = self._read_json(self.history_file)

        if "metrics" not in history_data:
            return []

        cutoff_time = datetime.now(UTC) - timedelta(hours=hours)
        filtered_metrics = []

        for metric_data in history_data["metrics"]:
            try:
                # Filter by time
                metric_time = datetime.fromisoformat(metric_data["timestamp"])
                if metric_time < cutoff_time:
                    continue

                # Filter by site if specified
                if site_id and metric_data.get("site_id") != site_id:
                    continue

                filtered_metrics.append(MECMetrics.from_dict(metric_data))

            except (KeyError, ValueError):
                # Skip invalid metric data
                continue

        # Sort by timestamp (newest first)
        filtered_metrics.sort(key=lambda m: m.timestamp, reverse=True)

        # Apply limit if specified
        if limit:
            filtered_metrics = filtered_metrics[:limit]

        return filtered_metrics

    def get_session_state(self, session_id: str) -> dict[str, Any]:
        """
        Get session state for Streamlit continuity.

        Args:
            session_id: Session identifier

        Returns:
            Session state dictionary
        """
        session_data = self._read_json(self.session_file)

        if session_data.get("session_id") == session_id:
            # Update last accessed time
            session_data["last_accessed"] = datetime.now(UTC).isoformat()
            self._write_json(self.session_file, session_data)
            return session_data.get("state", {})

        # Create new session
        return self._create_new_session(session_id)

    def _create_new_session(self, session_id: str) -> dict[str, Any]:
        """Create a new session with default state."""
        default_state = {
            "operation_mode": "normal",
            "selected_site": "MEC_A",
            "simulation_settings": {
                "latency_override": None,
                "cpu_override": None,
                "gpu_override": None,
                "queue_override": None,
            },
            "dashboard_settings": {
                "auto_refresh": True,
                "refresh_interval": 2,
                "show_thresholds": True,
                "chart_duration_minutes": 30,
            },
        }

        session_data = {
            "session_id": session_id,
            "created_at": datetime.now(UTC).isoformat(),
            "last_accessed": datetime.now(UTC).isoformat(),
            "state": default_state,
        }

        self._write_json(self.session_file, session_data)
        return default_state

    def update_session_state(
        self,
        session_id: str,
        state_updates: dict[str, Any],
    ) -> None:
        """
        Update session state.

        Args:
            session_id: Session identifier
            state_updates: Dictionary of state updates to apply
        """
        session_data = self._read_json(self.session_file)

        if session_data.get("session_id") != session_id:
            # Create new session if it doesn't exist
            self._create_new_session(session_id)
            session_data = self._read_json(self.session_file)

        # Deep merge state updates
        current_state = session_data.get("state", {})
        updated_state = self._deep_merge(current_state, state_updates)

        session_data["state"] = updated_state
        session_data["last_accessed"] = datetime.now(UTC).isoformat()

        self._write_json(self.session_file, session_data)

    def _deep_merge(
        self,
        base: dict[str, Any],
        updates: dict[str, Any],
    ) -> dict[str, Any]:
        """Deep merge two dictionaries."""
        result = base.copy()

        for key, value in updates.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def export_data(
        self,
        format_type: str = "json",
        site_id: str | None = None,
        hours: int = 24,
    ) -> str:
        """
        Export data for analysis.

        Args:
            format_type: Export format ("json" or "csv")
            site_id: Specific site ID, or None for all sites
            hours: Number of hours of data to export

        Returns:
            Path to exported file
        """
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        site_suffix = f"_{site_id}" if site_id else "_all_sites"

        if format_type.lower() == "csv":
            filename = f"metrics_export{site_suffix}_{timestamp}.csv"
            return self._export_csv(filename, site_id, hours)
        filename = f"metrics_export{site_suffix}_{timestamp}.json"
        return self._export_json(filename, site_id, hours)

    def _export_json(self, filename: str, site_id: str | None, hours: int) -> str:
        """Export data in JSON format."""
        export_path = self.data_dir / "exports" / filename

        # Get historical data
        metrics_history = self.get_metrics_history(site_id, hours)

        # Get current data
        current_metrics = self.get_current_metrics(site_id)

        export_data = {
            "export_info": {
                "timestamp": datetime.now(UTC).isoformat(),
                "site_id": site_id,
                "hours": hours,
                "total_records": len(metrics_history),
            },
            "current_metrics": (
                current_metrics.to_dict()
                if isinstance(current_metrics, MECMetrics)
                else current_metrics
            ),
            "historical_metrics": [m.to_dict() for m in metrics_history],
        }

        self._write_json(export_path, export_data)
        return str(export_path)

    def _export_csv(self, filename: str, site_id: str | None, hours: int) -> str:
        """Export data in CSV format."""

        export_path = self.data_dir / "exports" / filename
        metrics_history = self.get_metrics_history(site_id, hours)

        if not metrics_history:
            # Create empty CSV with headers
            with open(export_path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(
                    [
                        "site_id",
                        "timestamp",
                        "cpu_utilization",
                        "gpu_utilization",
                        "memory_utilization",
                        "queue_depth",
                        "response_time_ms",
                        "requests_per_second",
                        "active_connections",
                        "cache_hit_ratio",
                    ],
                )
            return str(export_path)

        with open(export_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)

            # Write header
            writer.writerow(
                [
                    "site_id",
                    "timestamp",
                    "cpu_utilization",
                    "gpu_utilization",
                    "memory_utilization",
                    "queue_depth",
                    "response_time_ms",
                    "requests_per_second",
                    "active_connections",
                    "cache_hit_ratio",
                    "network_latency_json",  # JSON string for complex data
                ],
            )

            # Write data rows
            for metrics in metrics_history:
                writer.writerow(
                    [
                        metrics.site_id,
                        metrics.timestamp.isoformat(),
                        metrics.cpu_utilization,
                        metrics.gpu_utilization,
                        metrics.memory_utilization,
                        metrics.queue_depth,
                        metrics.response_time_ms,
                        metrics.requests_per_second,
                        metrics.active_connections,
                        metrics.cache_hit_ratio,
                        json.dumps(metrics.network_latency),
                    ],
                )

        return str(export_path)

    def cleanup_old_data(self) -> dict[str, int]:
        """
        Clean up old data files and archive them.

        Returns:
            Dictionary with cleanup statistics
        """
        stats = {
            "archived_files": 0,
            "deleted_records": 0,
            "freed_space_mb": 0,
        }

        # Archive old export files (older than 30 days)
        exports_dir = self.data_dir / "exports"
        archive_dir = self.data_dir / "archive"
        cutoff_date = datetime.now(UTC) - timedelta(days=30)

        for export_file in exports_dir.glob("*.json"):
            try:
                file_time = datetime.fromtimestamp(export_file.stat().st_mtime, UTC)
                if file_time < cutoff_date:
                    # Move to archive
                    archive_path = archive_dir / export_file.name
                    shutil.move(str(export_file), str(archive_path))
                    stats["archived_files"] += 1
            except Exception:
                # Skip files that can't be processed
                continue

        # Clean up old CSV exports
        for csv_file in exports_dir.glob("*.csv"):
            try:
                file_time = datetime.fromtimestamp(csv_file.stat().st_mtime, UTC)
                if file_time < cutoff_date:
                    archive_path = archive_dir / csv_file.name
                    shutil.move(str(csv_file), str(archive_path))
                    stats["archived_files"] += 1
            except Exception:
                continue

        # Clean up historical metrics
        history_data = self._read_json(self.history_file)
        original_count = len(history_data.get("metrics", []))
        self._cleanup_old_history(history_data)
        self._write_json(self.history_file, history_data)

        new_count = len(history_data.get("metrics", []))
        stats["deleted_records"] = original_count - new_count

        return stats

    def get_storage_stats(self) -> dict[str, Any]:
        """
        Get storage statistics and health information.

        Returns:
            Dictionary with storage statistics
        """
        stats = {
            "data_directory": str(self.data_dir),
            "total_size_mb": 0,
            "file_counts": {},
            "oldest_record": None,
            "newest_record": None,
            "total_metrics_records": 0,
        }

        # Calculate directory sizes
        for path in self.data_dir.rglob("*"):
            if path.is_file():
                size_mb = path.stat().st_size / (1024 * 1024)
                stats["total_size_mb"] += size_mb

                # Count files by type
                suffix = path.suffix or "no_extension"
                stats["file_counts"][suffix] = stats["file_counts"].get(suffix, 0) + 1

        # Get metrics statistics
        history_data = self._read_json(self.history_file)
        metrics_list = history_data.get("metrics", [])
        stats["total_metrics_records"] = len(metrics_list)

        if metrics_list:
            timestamps = []
            for metric_data in metrics_list:
                try:
                    timestamps.append(datetime.fromisoformat(metric_data["timestamp"]))
                except (KeyError, ValueError):
                    continue

            if timestamps:
                stats["oldest_record"] = min(timestamps).isoformat()
                stats["newest_record"] = max(timestamps).isoformat()

        stats["total_size_mb"] = round(stats["total_size_mb"], 2)
        return stats


class StreamlitSessionManager:
    """
    Specialized session manager for Streamlit integration.

    Provides easy integration with Streamlit's session state
    and automatic persistence of dashboard settings.
    """

    def __init__(self, data_store: DataStore):
        self.data_store = data_store

    def get_session_id(self) -> str:
        """Generate or retrieve session ID for current Streamlit session."""
        import streamlit as st

        if "session_id" not in st.session_state:
            import uuid

            st.session_state.session_id = str(uuid.uuid4())

        return st.session_state.session_id

    def load_session_state(self) -> None:
        """Load persistent session state into Streamlit session state."""
        import streamlit as st

        session_id = self.get_session_id()
        persistent_state = self.data_store.get_session_state(session_id)

        # Merge persistent state into Streamlit session state
        for key, value in persistent_state.items():
            if key not in st.session_state:
                st.session_state[key] = value

    def save_session_state(self, keys_to_save: list[str] | None = None) -> None:
        """Save Streamlit session state to persistent storage."""
        import streamlit as st

        session_id = self.get_session_id()

        # Determine which keys to save
        if keys_to_save is None:
            # Save common dashboard state keys
            keys_to_save = [
                "operation_mode",
                "selected_site",
                "simulation_settings",
                "dashboard_settings",
                "auto_refresh",
                "refresh_interval",
            ]

        # Extract state to save
        state_updates = {}
        for key in keys_to_save:
            if key in st.session_state:
                state_updates[key] = st.session_state[key]

        if state_updates:
            self.data_store.update_session_state(session_id, state_updates)

    def clear_session(self) -> None:
        """Clear current session data."""
        import streamlit as st

        session_id = self.get_session_id()

        # Clear Streamlit session state
        for key in list(st.session_state.keys()):
            if key != "session_id":  # Keep session ID
                del st.session_state[key]

        # Create new persistent session
        self.data_store._create_new_session(session_id)
