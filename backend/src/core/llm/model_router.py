"""
Multi-LLM router for intelligent model selection and load balancing.
"""

import yaml
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class Provider(Enum):
    """LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    COHERE = "cohere"
    LOCAL_LLAMA = "local_llama"
    HUGGINGFACE = "huggingface"

class LoadBalancingStrategy(Enum):
    """Load balancing strategies."""
    ROUND_ROBIN = "round_robin"
    LEAST_LATENCY = "least_latency"
    WEIGHTED = "weighted"
    RANDOM = "random"

@dataclass
class Model:
    """LLM model configuration."""
    provider: str
    model_name: str
    display_name: str
    description: str
    max_tokens: int
    temperature: float
    cost_per_1k_tokens: float
    latency_ms: int
    capabilities: List[str]
    enabled: bool
    requires_api_key: bool
    priority: int
    metrics: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize metrics if not provided."""
        if not self.metrics:
            self.metrics = {
                "total_requests": 0,
                "total_tokens": 0,
                "avg_latency": self.latency_ms,
                "success_rate": 100.0,
                "cost_today": 0.0,
                "last_used": None
            }

@dataclass
class RoutingRule:
    """Rule for routing requests to specific models."""
    name: str
    conditions: Dict[str, Any]
    model: str
    priority: int
    fallback: Optional[str] = None

class ModelRouter:
    """Router for selecting and managing LLM models."""
    
    def __init__(self, config_path: str):
        """Initialize model router."""
        self.config_path = Path(config_path)
        self.models: Dict[str, Model] = {}
        self.routing_rules: List[RoutingRule] = []
        self.load_balancing_config: Dict[str, Any] = {}
        self._load_configuration()
    
    def _load_configuration(self):
        """Load models and routing configuration."""
        try:
            if not self.config_path.exists():
                logger.warning(f"Models config file not found: {self.config_path}")
                return
            
            with open(self.config_path, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
            
            # Load models
            models_data = config.get('models', [])
            for model_data in models_data:
                model = Model(
                    provider=model_data['provider'],
                    model_name=model_data['model_name'],
                    display_name=model_data['display_name'],
                    description=model_data['description'],
                    max_tokens=model_data['max_tokens'],
                    temperature=model_data['temperature'],
                    cost_per_1k_tokens=model_data['cost_per_1k_tokens'],
                    latency_ms=model_data['latency_ms'],
                    capabilities=model_data['capabilities'],
                    enabled=model_data['enabled'],
                    requires_api_key=model_data['requires_api_key'],
                    priority=model_data['priority']
                )
                self.models[model.model_name] = model
            
            # Load routing rules
            routing_rules_data = config.get('routing_rules', {})
            for rule_name, rule_data in routing_rules_data.items():
                rule = RoutingRule(
                    name=rule_name,
                    conditions=rule_data,
                    model=rule_data['model'],
                    priority=rule_data['priority'],
                    fallback=rule_data.get('fallback')
                )
                self.routing_rules.append(rule)
            
            # Load balancing configuration
            self.load_balancing_config = config.get('load_balancing', {
                'strategy': 'round_robin',
                'health_check_interval': 60,
                'max_retries': 3,
                'retry_delay': 1
            })
            
            logger.info(f"Loaded {len(self.models)} models and {len(self.routing_rules)} routing rules")
            
        except Exception as e:
            logger.error(f"Error loading model configuration: {e}")
            # Continue with empty configuration for development
    
    def get_model(self, model_name: str) -> Optional[Model]:
        """Get model by name."""
        return self.models.get(model_name)
    
    def get_enabled_models(self) -> List[Model]:
        """Get all enabled models."""
        return [model for model in self.models.values() if model.enabled]
    
    def get_models_by_capability(self, capability: str) -> List[Model]:
        """Get models that have a specific capability."""
        return [
            model for model in self.models.values()
            if capability in model.capabilities and model.enabled
        ]
    
    def select_model(self, 
                    query: str = None,
                    document_type: str = None,
                    complexity: str = "medium",
                    max_cost: float = None,
                    max_latency: int = None) -> Optional[Model]:
        """Select the best model based on criteria."""
        
        # Apply routing rules first
        for rule in sorted(self.routing_rules, key=lambda x: x.priority):
            if self._matches_routing_rule(rule, query, document_type, complexity):
                model = self.get_model(rule.model)
                if model and model.enabled:
                    return model
                elif rule.fallback:
                    fallback_model = self.get_model(rule.fallback)
                    if fallback_model and fallback_model.enabled:
                        return fallback_model
        
        # Fallback to general selection
        available_models = self.get_enabled_models()
        
        if not available_models:
            return None
        
        # Filter by constraints
        if max_cost is not None:
            available_models = [m for m in available_models if m.cost_per_1k_tokens <= max_cost]
        
        if max_latency is not None:
            available_models = [m for m in available_models if m.latency_ms <= max_latency]
        
        if not available_models:
            return None
        
        # Select based on load balancing strategy
        strategy = self.load_balancing_config.get('strategy', 'round_robin')
        
        if strategy == 'least_latency':
            return min(available_models, key=lambda m: m.metrics.get('avg_latency', m.latency_ms))
        elif strategy == 'weighted':
            # Simple priority-based selection
            return max(available_models, key=lambda m: m.priority)
        else:  # round_robin or default
            # Simple first available for now
            return available_models[0]
    
    def _matches_routing_rule(self, rule: RoutingRule, query: str, document_type: str, complexity: str) -> bool:
        """Check if request matches routing rule conditions."""
        conditions = rule.conditions
        
        # Check document classification
        if 'document_classification' in conditions:
            if document_type in conditions['document_classification']:
                return True
        
        # Check query complexity
        if 'query_complexity' in conditions:
            if complexity == conditions['query_complexity']:
                return True
        
        # Check response time requirement
        if 'response_time_requirement' in conditions:
            if conditions['response_time_requirement'] == 'fast' and complexity == 'low':
                return True
        
        return False
    
    def toggle_model(self, model_name: str) -> bool:
        """Toggle model enabled state."""
        if model_name in self.models:
            self.models[model_name].enabled = not self.models[model_name].enabled
            logger.info(f"Model {model_name} {'enabled' if self.models[model_name].enabled else 'disabled'}")
            return True
        return False
    
    def update_model_metrics(self, model_name: str, metrics: Dict[str, Any]):
        """Update model metrics."""
        if model_name in self.models:
            self.models[model_name].metrics.update(metrics)
    
    def get_router_stats(self) -> Dict[str, Any]:
        """Get router statistics."""
        total_models = len(self.models)
        enabled_models = len(self.get_enabled_models())
        
        providers = set(model.provider for model in self.models.values())
        capabilities = set()
        for model in self.models.values():
            capabilities.update(model.capabilities)
        
        total_requests = sum(model.metrics.get('total_requests', 0) for model in self.models.values())
        total_tokens = sum(model.metrics.get('total_tokens', 0) for model in self.models.values())
        
        return {
            "total_models": total_models,
            "enabled_models": enabled_models,
            "disabled_models": total_models - enabled_models,
            "providers": list(providers),
            "capabilities": list(capabilities),
            "routing_rules": len(self.routing_rules),
            "total_requests": total_requests,
            "total_tokens": total_tokens,
            "load_balancing_strategy": self.load_balancing_config.get('strategy', 'round_robin')
        }