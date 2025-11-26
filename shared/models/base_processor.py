"""
Base processor class with robust initialization and error handling
All model processors should inherit from this for consistency
"""
import logging
import time
from typing import Dict, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class ProcessorInitializationError(Exception):
    """Raised when a processor fails to initialize properly"""
    pass


class ProcessorHealthCheckError(Exception):
    """Raised when a processor health check fails"""
    pass


class BaseProcessor(ABC):
    """
    Base class for all model processors with robust initialization

    Features:
    - Health checks before use
    - Initialization validation
    - Standardized error handling
    - Resource status tracking
    """

    def __init__(self, model_config: Dict):
        self.model_config = model_config
        self.model_name = model_config.get('name', 'unknown')
        self.model_id = model_config.get('id', 'unknown')
        self.initialized = False
        self.initialization_error = None
        self.last_health_check = None

    @abstractmethod
    def _load_model(self):
        """
        Load the model and initialize resources
        Must be implemented by subclasses
        Should raise ProcessorInitializationError on failure
        """
        pass

    @abstractmethod
    def _health_check(self) -> bool:
        """
        Verify the processor is ready to handle requests
        Must be implemented by subclasses
        Should return True if healthy, False otherwise
        """
        pass

    @abstractmethod
    def extract(self, image_path: str) -> 'ExtractionResult':
        """
        Extract receipt data from image
        Must be implemented by subclasses
        Returns ExtractionResult with success status and data or error
        """
        pass

    def initialize(self, retry_count: int = 2):
        """
        Initialize the processor with retry logic

        Args:
            retry_count: Number of times to retry initialization on failure

        Raises:
            ProcessorInitializationError: If initialization fails after retries
        """
        for attempt in range(retry_count + 1):
            try:
                logger.info(f"Initializing {self.model_name} (attempt {attempt + 1}/{retry_count + 1})")
                self._load_model()

                # Verify initialization with health check
                if not self._health_check():
                    raise ProcessorInitializationError(
                        f"{self.model_name} loaded but failed health check"
                    )

                self.initialized = True
                self.initialization_error = None
                logger.info(f"{self.model_name} initialized successfully")
                return

            except Exception as e:
                logger.error(f"Initialization attempt {attempt + 1} failed: {e}")
                self.initialization_error = str(e)

                if attempt < retry_count:
                    # Wait before retry (exponential backoff)
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    # Final attempt failed
                    error_msg = (
                        f"Failed to initialize {self.model_name} after {retry_count + 1} attempts. "
                        f"Last error: {e}"
                    )
                    raise ProcessorInitializationError(error_msg) from e

    def ensure_healthy(self):
        """
        Ensure processor is initialized and healthy before use

        Raises:
            ProcessorHealthCheckError: If health check fails
        """
        if not self.initialized:
            raise ProcessorHealthCheckError(
                f"{self.model_name} is not initialized. "
                f"Initialization error: {self.initialization_error}"
            )

        if not self._health_check():
            raise ProcessorHealthCheckError(
                f"{self.model_name} health check failed"
            )

        self.last_health_check = time.time()

    def get_status(self) -> Dict:
        """Get current processor status for monitoring"""
        return {
            'model_name': self.model_name,
            'model_id': self.model_id,
            'initialized': self.initialized,
            'initialization_error': self.initialization_error,
            'last_health_check': self.last_health_check,
            'healthy': self._health_check() if self.initialized else False
        }
