# src/financial_data_collector/core/exceptions.py

"""
Custom exceptions for the Financial Data Collector application.

This module defines domain-specific exceptions used throughout the application
for better error handling and debugging.
"""
import asyncio

class FinancialDataCollectorError(Exception):
    """
    Base exception for all Financial Data Collector errors.
    
    All custom exceptions should inherit from this class to allow
    catching all application-specific errors.
    """
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self):
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


class ConfigError(FinancialDataCollectorError):
    """
    Exception raised for configuration-related errors.
    
    Examples:
        - Missing required configuration keys
        - Invalid configuration values
        - Configuration file not found
        - YAML/JSON parsing errors
    """
    pass


class DependencyError(FinancialDataCollectorError):
    """
    Exception raised for dependency-related errors.
    
    Examples:
        - Required dependency not found
        - Dependency initialization failed
        - Circular dependency detected
        - Dependency version mismatch
    """
    pass


class ModuleError(FinancialDataCollectorError):
    """
    Exception raised for module-related errors.
    
    Examples:
        - Module initialization failed
        - Module start/stop errors
        - Module health check failures
    """
    def __init__(self, message: str, module_name: str = None, details: dict = None):
        self.module_name = module_name
        super().__init__(message, details)
    
    def __str__(self):
        base_msg = f"Module '{self.module_name}': {self.message}" if self.module_name else self.message
        if self.details:
            return f"{base_msg} | Details: {self.details}"
        return base_msg


class StorageError(FinancialDataCollectorError):
    """
    Exception raised for storage-related errors.
    
    Examples:
        - Database connection failed
        - Query execution failed
        - Data persistence errors
    """
    pass


class DataCollectionError(FinancialDataCollectorError):
    """
    Exception raised for data collection errors.
    
    Examples:
        - API request failed
        - Data parsing errors
        - Invalid data format
    """
    pass


class ValidationError(FinancialDataCollectorError):
    """
    Exception raised for data validation errors.
    
    Examples:
        - Invalid data schema
        - Missing required fields
        - Data type mismatch
    """
    def __init__(self, message: str, field: str = None, value: any = None, details: dict = None):
        self.field = field
        self.value = value
        super().__init__(message, details)
    
    def __str__(self):
        parts = [self.message]
        if self.field:
            parts.append(f"Field: {self.field}")
        if self.value is not None:
            parts.append(f"Value: {self.value}")
        if self.details:
            parts.append(f"Details: {self.details}")
        return " | ".join(parts)


class AuthenticationError(FinancialDataCollectorError):
    """
    Exception raised for authentication errors.
    
    Examples:
        - Invalid credentials
        - Token expired
        - Insufficient permissions
    """
    pass


class RateLimitError(FinancialDataCollectorError):
    """
    Exception raised when rate limits are exceeded.
    
    Examples:
        - API rate limit exceeded
        - Too many requests
    """
    def __init__(self, message: str, retry_after: int = None, details: dict = None):
        self.retry_after = retry_after
        super().__init__(message, details)
    
    def __str__(self):
        base_msg = self.message
        if self.retry_after:
            base_msg += f" | Retry after: {self.retry_after}s"
        if self.details:
            base_msg += f" | Details: {self.details}"
        return base_msg


class NetworkError(FinancialDataCollectorError):
    """
    Exception raised for network-related errors.
    
    Examples:
        - Connection timeout
        - Network unreachable
        - DNS resolution failed
    """
    pass


class TimeoutError(FinancialDataCollectorError):
    """
    Exception raised when operations timeout.
    
    Examples:
        - Database query timeout
        - API request timeout
        - Module start timeout
    """
    def __init__(self, message: str, timeout_seconds: float = None, details: dict = None):
        self.timeout_seconds = timeout_seconds
        super().__init__(message, details)
    
    def __str__(self):
        base_msg = self.message
        if self.timeout_seconds:
            base_msg += f" | Timeout: {self.timeout_seconds}s"
        if self.details:
            base_msg += f" | Details: {self.details}"
        return base_msg


class PluginError(FinancialDataCollectorError):
    """
    Exception raised for plugin-related errors.
    
    Examples:
        - Plugin not found
        - Plugin initialization failed
        - Invalid plugin interface
    """
    def __init__(self, message: str, plugin_name: str = None, details: dict = None):
        self.plugin_name = plugin_name
        super().__init__(message, details)
    
    def __str__(self):
        base_msg = f"Plugin '{self.plugin_name}': {self.message}" if self.plugin_name else self.message
        if self.details:
            return f"{base_msg} | Details: {self.details}"
        return base_msg


class DataIntegrityError(FinancialDataCollectorError):
    """
    Exception raised for data integrity violations.
    
    Examples:
        - Duplicate key violation
        - Foreign key constraint violation
        - Check constraint violation
    """
    pass


class ResourceExhaustedError(FinancialDataCollectorError):
    """
    Exception raised when system resources are exhausted.
    
    Examples:
        - Out of memory
        - Connection pool exhausted
        - Disk space full
    """
    def __init__(self, message: str, resource_type: str = None, details: dict = None):
        self.resource_type = resource_type
        super().__init__(message, details)
    
    def __str__(self):
        base_msg = self.message
        if self.resource_type:
            base_msg += f" | Resource: {self.resource_type}"
        if self.details:
            base_msg += f" | Details: {self.details}"
        return base_msg


class InitializationError(FinancialDataCollectorError):
    """
    Exception raised when component initialization fails.
    
    Examples:
        - Component setup failed
        - Required resources unavailable
        - Initialization sequence error
    """
    def __init__(self, message: str, component: str = None, details: dict = None):
        self.component = component
        super().__init__(message, details)
    
    def __str__(self):
        base_msg = f"Component '{self.component}': {self.message}" if self.component else self.message
        if self.details:
            return f"{base_msg} | Details: {self.details}"
        return base_msg


class ShutdownError(FinancialDataCollectorError):
    """
    Exception raised when graceful shutdown fails.
    
    Examples:
        - Component failed to stop
        - Resource cleanup failed
        - Shutdown timeout
    """
    pass


class ModuleInitializationError(Exception):
    """模块初始化失败异常"""
    pass

class ModuleStartError(Exception):
    """模块启动失败异常"""
    pass

class ModuleDependencyError(Exception):
    """模块依赖关系异常"""
    pass