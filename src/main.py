"""
MEC Inference Routing System - Main Orchestrator Entry Point
MEC-native orchestration without cloud dependencies
"""

import asyncio
import logging
from datetime import UTC, datetime

from device.edge_interface import EdgeInterface
from orchestrator.mec_orchestrator import MECOrchestrator
from swarm.swarm_coordinator import SwarmCoordinator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class MECSystem:
    """Main MEC system coordinator"""

    def __init__(self):
        self.orchestrator = MECOrchestrator()
        self.swarm_coordinator = SwarmCoordinator()
        self.edge_interface = EdgeInterface()
        self.running = False

    async def start(self):
        """Start the MEC system"""
        logger.info("Starting MEC Inference Routing System...")

        try:
            # Initialize components
            await self.orchestrator.initialize()
            await self.swarm_coordinator.initialize()
            await self.edge_interface.initialize()

            self.running = True
            logger.info("MEC system started successfully")

            # Start main processing loop
            await self._main_loop()

        except Exception:
            logger.exception("Failed to start MEC system")
            raise

    async def stop(self):
        """Stop the MEC system"""
        logger.info("Stopping MEC system...")
        self.running = False

        await self.orchestrator.shutdown()
        await self.swarm_coordinator.shutdown()
        await self.edge_interface.shutdown()

        logger.info("MEC system stopped")

    async def _main_loop(self):
        """Main processing loop"""
        while self.running:
            try:
                # Check for incoming requests
                requests = await self.edge_interface.get_pending_requests()

                for request in requests:
                    await self._process_request(request)

                # Perform swarm coordination
                await self.swarm_coordinator.coordinate()

                # Update metrics
                await self.orchestrator.update_metrics()

                # Sleep briefly to prevent busy waiting
                await asyncio.sleep(0.1)

            except Exception:
                logger.exception("Error in main loop")
                await asyncio.sleep(1)

    async def _process_request(self, request: dict):
        """Process a single inference request"""
        try:
            # Route through orchestrator
            routing_decision = await self.orchestrator.route_request(request)

            # Execute based on routing decision
            if routing_decision["target"] == "local":
                result = await self._process_locally(request)
            elif routing_decision["target"] == "swarm":
                result = await self.swarm_coordinator.process_request(request)
            else:
                result = await self._process_cloud_fallback(request)

            # Send response back to edge device
            await self.edge_interface.send_response(request["id"], result)

        except Exception as e:
            logger.exception("Error processing request %s", request.get("id"))
            await self.edge_interface.send_error(request["id"], str(e))

    async def _process_locally(self, request: dict) -> dict:
        """Process request locally on this MEC site"""
        return {
            "result": f"Processed locally: {request['content'][:50]}...",
            "latency_ms": 25,
            "processing_site": "local",
            "timestamp": datetime.now(UTC).isoformat(),
        }

    async def _process_cloud_fallback(self, request: dict) -> dict:
        """Process request via cloud fallback"""
        return {
            "result": f"Processed via cloud: {request['content'][:50]}...",
            "latency_ms": 150,
            "processing_site": "cloud",
            "timestamp": datetime.now(UTC).isoformat(),
        }


async def main():
    """Main entry point"""
    system = MECSystem()

    try:
        await system.start()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    finally:
        await system.stop()


if __name__ == "__main__":
    # Run the MEC system
    asyncio.run(main())
