"""
Error Recovery and Robust Error Handling for Market Voices
Provides circuit breaker pattern, error classification, graceful degradation, and automatic recovery
"""
import time
import asyncio
from typing import Dict, List, Optional, Callable, Any, Union
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from loguru import logger
import threading
from functools import wraps
import traceback

from ..config.settings import get_settings


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorType(Enum):
    """Error types for classification"""
    RATE_LIMIT = "rate_limit"
    NETWORK = "network"
    AUTHENTICATION = "authentication"
    VALIDATION = "validation"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


@dataclass
class ErrorInfo:
    """Information about an error"""
    error_type: ErrorType
    severity: ErrorSeverity
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    retry_count: int = 0
    max_retries: int = 3
    recovery_strategy: str = "retry"
    context: Dict[str, Any] = field(default_factory=dict)


class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service is recovered


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5
    recovery_timeout: int = 60  # seconds
    expected_exception: type = Exception
    monitor_interval: int = 10  # seconds


class CircuitBreaker:
    """Circuit breaker pattern implementation"""
    
    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.last_success_time = None
        self._lock = threading.Lock()
        
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self._set_half_open()
            else:
                raise Exception(f"Circuit breaker {self.name} is OPEN - service unavailable")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.config.expected_exception as e:
            self._on_failure(e)
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return True
        return datetime.now() - self.last_failure_time > timedelta(seconds=self.config.recovery_timeout)
    
    def _set_half_open(self):
        """Set circuit breaker to half-open state"""
        with self._lock:
            self.state = CircuitBreakerState.HALF_OPEN
            logger.info(f"Circuit breaker {self.name} set to HALF_OPEN")
    
    def _on_success(self):
        """Handle successful call"""
        with self._lock:
            self.failure_count = 0
            self.last_success_time = datetime.now()
            if self.state == CircuitBreakerState.HALF_OPEN:
                self.state = CircuitBreakerState.CLOSED
                logger.info(f"Circuit breaker {self.name} reset to CLOSED")
    
    def _on_failure(self, error: Exception):
        """Handle failed call"""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = datetime.now()
            
            if self.state == CircuitBreakerState.HALF_OPEN or self.failure_count >= self.config.failure_threshold:
                self.state = CircuitBreakerState.OPEN
                logger.warning(f"Circuit breaker {self.name} opened after {self.failure_count} failures")
    
    def get_status(self) -> Dict[str, Any]:
        """Get circuit breaker status"""
        return {
            'name': self.name,
            'state': self.state.value,
            'failure_count': self.failure_count,
            'last_failure_time': self.last_failure_time.isoformat() if self.last_failure_time else None,
            'last_success_time': self.last_success_time.isoformat() if self.last_success_time else None
        }


class ErrorClassifier:
    """Classify errors by type and severity"""
    
    @staticmethod
    def classify_error(error: Exception, context: Dict[str, Any] = None) -> ErrorInfo:
        """Classify an error based on its type and context"""
        error_str = str(error).lower()
        
        # Determine error type
        if any(phrase in error_str for phrase in ['429', 'rate limit', 'too many requests']):
            error_type = ErrorType.RATE_LIMIT
            severity = ErrorSeverity.MEDIUM
            recovery_strategy = "backoff_retry"
        elif any(phrase in error_str for phrase in ['timeout', 'timed out', 'connection']):
            error_type = ErrorType.TIMEOUT
            severity = ErrorSeverity.MEDIUM
            recovery_strategy = "retry"
        elif any(phrase in error_str for phrase in ['network', 'connection refused', 'dns']):
            error_type = ErrorType.NETWORK
            severity = ErrorSeverity.HIGH
            recovery_strategy = "retry_with_backoff"
        elif any(phrase in error_str for phrase in ['401', '403', 'unauthorized', 'forbidden']):
            error_type = ErrorType.AUTHENTICATION
            severity = ErrorSeverity.CRITICAL
            recovery_strategy = "manual_intervention"
        elif any(phrase in error_str for phrase in ['validation', 'invalid', 'malformed']):
            error_type = ErrorType.VALIDATION
            severity = ErrorSeverity.LOW
            recovery_strategy = "skip"
        else:
            error_type = ErrorType.UNKNOWN
            severity = ErrorSeverity.MEDIUM
            recovery_strategy = "retry"
        
        return ErrorInfo(
            error_type=error_type,
            severity=severity,
            message=str(error),
            recovery_strategy=recovery_strategy,
            context=context or {}
        )


class ErrorRecoveryManager:
    """Manages error recovery strategies and automatic recovery"""
    
    def __init__(self):
        self.settings = get_settings()
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.error_history: List[ErrorInfo] = []
        self.recovery_strategies: Dict[str, Callable] = {}
        self._lock = threading.Lock()
        
        # Initialize default recovery strategies
        self._init_recovery_strategies()
        
    def _init_recovery_strategies(self):
        """Initialize default recovery strategies"""
        self.recovery_strategies = {
            "retry": self._retry_strategy,
            "backoff_retry": self._exponential_backoff_retry,
            "retry_with_backoff": self._exponential_backoff_retry,
            "skip": self._skip_strategy,
            "manual_intervention": self._manual_intervention_strategy,
            "fallback": self._fallback_strategy
        }
    
    def get_or_create_circuit_breaker(self, name: str, config: CircuitBreakerConfig = None) -> CircuitBreaker:
        """Get or create a circuit breaker for a service"""
        if config is None:
            config = CircuitBreakerConfig()
        
        with self._lock:
            if name not in self.circuit_breakers:
                self.circuit_breakers[name] = CircuitBreaker(name, config)
            return self.circuit_breakers[name]
    
    def handle_error(self, error: Exception, context: Dict[str, Any] = None) -> ErrorInfo:
        """Handle an error with classification and recovery"""
        error_info = ErrorClassifier.classify_error(error, context)
        
        with self._lock:
            self.error_history.append(error_info)
            
            # Keep only recent errors (last 100)
            if len(self.error_history) > 100:
                self.error_history = self.error_history[-100:]
        
        logger.warning(f"Error handled: {error_info.error_type.value} - {error_info.severity.value} - {error_info.message}")
        
        # Execute recovery strategy
        self._execute_recovery_strategy(error_info)
        
        return error_info
    
    def _execute_recovery_strategy(self, error_info: ErrorInfo):
        """Execute the appropriate recovery strategy"""
        strategy = self.recovery_strategies.get(error_info.recovery_strategy)
        if strategy:
            try:
                strategy(error_info)
            except Exception as e:
                logger.error(f"Recovery strategy failed: {str(e)}")
        else:
            logger.warning(f"Unknown recovery strategy: {error_info.recovery_strategy}")
    
    def _retry_strategy(self, error_info: ErrorInfo):
        """Simple retry strategy"""
        if error_info.retry_count < error_info.max_retries:
            error_info.retry_count += 1
            logger.info(f"Retrying operation (attempt {error_info.retry_count}/{error_info.max_retries})")
            time.sleep(1)  # Simple delay
        else:
            logger.error(f"Max retries exceeded for error: {error_info.message}")
    
    def _exponential_backoff_retry(self, error_info: ErrorInfo):
        """Exponential backoff retry strategy"""
        if error_info.retry_count < error_info.max_retries:
            error_info.retry_count += 1
            delay = min(2 ** error_info.retry_count, 60)  # Cap at 60 seconds
            logger.info(f"Retrying with exponential backoff: {delay}s (attempt {error_info.retry_count}/{error_info.max_retries})")
            time.sleep(delay)
        else:
            logger.error(f"Max retries exceeded for error: {error_info.message}")
    
    def _skip_strategy(self, error_info: ErrorInfo):
        """Skip the operation"""
        logger.info(f"Skipping operation due to error: {error_info.message}")
    
    def _manual_intervention_strategy(self, error_info: ErrorInfo):
        """Require manual intervention"""
        logger.critical(f"Manual intervention required for error: {error_info.message}")
        # Could send alert/notification here
    
    def _fallback_strategy(self, error_info: ErrorInfo):
        """Use fallback mechanism"""
        logger.info(f"Using fallback mechanism for error: {error_info.message}")
        # Implement fallback logic here
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of recent errors"""
        with self._lock:
            recent_errors = [e for e in self.error_history 
                           if datetime.now() - e.timestamp < timedelta(hours=1)]
            
            error_counts = {}
            severity_counts = {}
            
            for error in recent_errors:
                error_counts[error.error_type.value] = error_counts.get(error.error_type.value, 0) + 1
                severity_counts[error.severity.value] = severity_counts.get(error.severity.value, 0) + 1
            
            return {
                'total_errors': len(recent_errors),
                'error_types': error_counts,
                'severity_levels': severity_counts,
                'circuit_breakers': {name: cb.get_status() for name, cb in self.circuit_breakers.items()}
            }


class GracefulDegradation:
    """Implements graceful degradation strategies"""
    
    def __init__(self, error_manager: ErrorRecoveryManager):
        self.error_manager = error_manager
        self.fallback_data = {}
        self.degradation_levels = {
            'full': 1.0,
            'reduced': 0.7,
            'minimal': 0.3,
            'emergency': 0.1
        }
    
    def with_fallback(self, primary_func: Callable, fallback_func: Callable, 
                     fallback_key: str = None):
        """Execute function with fallback"""
        def wrapper(*args, **kwargs):
            try:
                return primary_func(*args, **kwargs)
            except Exception as e:
                error_info = self.error_manager.handle_error(e)
                
                if error_info.severity == ErrorSeverity.CRITICAL:
                    logger.warning(f"Using fallback for critical error: {error_info.message}")
                    return fallback_func(*args, **kwargs)
                else:
                    raise
        
        return wrapper
    
    def with_cached_fallback(self, func: Callable, cache_key: str, 
                           cache_duration: int = 3600):
        """Execute function with cached fallback"""
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                # Cache successful result
                self.fallback_data[cache_key] = {
                    'data': result,
                    'timestamp': datetime.now()
                }
                return result
            except Exception as e:
                error_info = self.error_manager.handle_error(e)
                
                # Try to use cached data
                if cache_key in self.fallback_data:
                    cached = self.fallback_data[cache_key]
                    if datetime.now() - cached['timestamp'] < timedelta(seconds=cache_duration):
                        logger.info(f"Using cached data for {cache_key}")
                        return cached['data']
                
                raise
        
        return wrapper


# Global error recovery manager
error_recovery_manager = ErrorRecoveryManager()
graceful_degradation = GracefulDegradation(error_recovery_manager)


def with_error_recovery(func: Callable = None, *, 
                       circuit_breaker_name: str = None,
                       max_retries: int = 3,
                       fallback_func: Callable = None):
    """Decorator for automatic error recovery"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Get circuit breaker if specified
            cb = None
            if circuit_breaker_name:
                cb = error_recovery_manager.get_or_create_circuit_breaker(circuit_breaker_name)
            
            try:
                if cb:
                    return cb.call(f, *args, **kwargs)
                else:
                    return f(*args, **kwargs)
            except Exception as e:
                error_info = error_recovery_manager.handle_error(e, {
                    'function': f.__name__,
                    'args': str(args),
                    'kwargs': str(kwargs)
                })
                
                # Try fallback if available
                if fallback_func and error_info.retry_count >= error_info.max_retries:
                    logger.info(f"Using fallback function for {f.__name__}")
                    return fallback_func(*args, **kwargs)
                
                raise
        
        return wrapper
    
    if func is None:
        return decorator
    return decorator(func)


def with_graceful_degradation(primary_func: Callable, fallback_func: Callable):
    """Decorator for graceful degradation"""
    return graceful_degradation.with_fallback(primary_func, fallback_func)


def with_cached_fallback(func: Callable, cache_key: str, cache_duration: int = 3600):
    """Decorator for cached fallback"""
    return graceful_degradation.with_cached_fallback(func, cache_key, cache_duration) 