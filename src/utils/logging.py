"""
Structured logging utilities for the trading system.
"""
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class StructuredLogger:
    """Structured logger with JSON output support."""
    
    def __init__(
        self,
        name: str,
        level: str = "INFO",
        output_format: str = "json",
        log_file: Optional[str] = None
    ):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        self.output_format = output_format
        
        # Remove existing handlers
        self.logger.handlers.clear()
        
        # Console handler
        if log_file == "stdout":
            handler = logging.StreamHandler(sys.stdout)
        elif log_file:
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)
            handler = logging.FileHandler(log_file)
        else:
            handler = logging.StreamHandler(sys.stdout)
        
        if output_format == "json":
            handler.setFormatter(JSONFormatter())
        else:
            handler.setFormatter(
                logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
            )
        
        self.logger.addHandler(handler)
    
    def _log(self, level: str, message: str, **kwargs: Any) -> None:
        """Internal log method with structured data."""
        extra = {"structured_data": kwargs} if kwargs else {}
        getattr(self.logger, level.lower())(message, extra=extra)
    
    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        self._log("DEBUG", message, **kwargs)
    
    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        self._log("INFO", message, **kwargs)
    
    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        self._log("WARNING", message, **kwargs)
    
    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message."""
        self._log("ERROR", message, **kwargs)
    
    def critical(self, message: str, **kwargs: Any) -> None:
        """Log critical message."""
        self._log("CRITICAL", message, **kwargs)


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add structured data if present
        if hasattr(record, "structured_data"):
            log_data.update(record.structured_data)
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


class AuditLogger:
    """Audit logger for compliance and traceability."""
    
    def __init__(self, log_file: str = "logs/audit.log"):
        self.logger = StructuredLogger(
            "audit",
            level="INFO",
            output_format="json",
            log_file=log_file
        )
    
    def log_decision(
        self,
        decision_type: str,
        strategy_id: str,
        inputs: Dict[str, Any],
        output: Dict[str, Any],
        model_version: str,
        config_version: str
    ) -> None:
        """Log a trading decision for audit trail."""
        self.logger.info(
            "Trading decision",
            decision_type=decision_type,
            strategy_id=strategy_id,
            inputs=inputs,
            output=output,
            model_version=model_version,
            config_version=config_version
        )
    
    def log_order(
        self,
        order_id: str,
        symbol: str,
        side: str,
        quantity: int,
        price: Optional[float],
        strategy_id: str
    ) -> None:
        """Log an order for audit trail."""
        self.logger.info(
            "Order placed",
            order_id=order_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=price,
            strategy_id=strategy_id
        )
    
    def log_fill(
        self,
        fill_id: str,
        order_id: str,
        symbol: str,
        quantity: int,
        price: float,
        commission: float
    ) -> None:
        """Log a fill for audit trail."""
        self.logger.info(
            "Order filled",
            fill_id=fill_id,
            order_id=order_id,
            symbol=symbol,
            quantity=quantity,
            price=price,
            commission=commission
        )
    
    def log_risk_breach(
        self,
        breach_type: str,
        current_value: float,
        limit: float,
        action_taken: str
    ) -> None:
        """Log a risk limit breach."""
        self.logger.warning(
            "Risk limit breach",
            breach_type=breach_type,
            current_value=current_value,
            limit=limit,
            action_taken=action_taken
        )


# Global logger instances
def get_logger(name: str, **kwargs: Any) -> StructuredLogger:
    """Get or create a logger instance."""
    return StructuredLogger(name, **kwargs)
