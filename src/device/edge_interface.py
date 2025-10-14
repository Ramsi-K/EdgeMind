"""
Edge Interface - Device communication layer
"""

import logging

logger = logging.getLogger(__name__)


class EdgeInterface:
    """Interface for edge device communication"""

    def __init__(self):
        self.running = False
        self.pending_requests = []

    async def initialize(self):
        """Initialize the edge interface"""
        logger.info("Initializing Edge Interface")
        self.running = True

    async def shutdown(self):
        """Shutdown the edge interface"""
        logger.info("Shutting down Edge Interface")
        self.running = False

    async def get_pending_requests(self) -> list[dict]:
        """Get pending requests from edge devices"""
        # Mock request generation for demo
        if len(self.pending_requests) < 5:
            self.pending_requests.append(
                {
                    "id": f"req_{len(self.pending_requests)}",
                    "content": "Sample request content",
                    "timestamp": "2024-01-01T00:00:00Z",
                },
            )

        # Return and clear requests
        requests = self.pending_requests.copy()
        self.pending_requests.clear()
        return requests

    async def send_response(self, request_id: str, result: dict):
        """Send response back to edge device"""
        logger.info("Sent response for request %s", request_id)

    async def send_error(self, request_id: str, error: str):
        """Send error response to edge device"""
        logger.error("Sent error for request %s: %s", request_id, error)
