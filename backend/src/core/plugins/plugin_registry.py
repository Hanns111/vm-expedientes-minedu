"""
Plugin registry for managing and loading plugins.
"""

import yaml
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

@dataclass
class Plugin:
    """Plugin configuration and metadata."""
    id: str
    name: str
    description: str
    version: str
    capabilities: List[str]
    endpoint: str
    enabled: bool
    auth_required: bool
    max_file_size_mb: int
    timeout_seconds: int
    rate_limit_per_minute: int
    config: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize metrics if not provided."""
        if not self.metrics:
            self.metrics = {
                "total_requests": 0,
                "success_rate": 100.0,
                "avg_latency": 200,
                "errors_last_hour": 0,
                "last_used": None
            }

class PluginRegistry:
    """Registry for managing plugins."""
    
    def __init__(self, config_path: str):
        """Initialize plugin registry."""
        self.config_path = Path(config_path)
        self.plugins: Dict[str, Plugin] = {}
        self._load_plugins()
    
    def _load_plugins(self):
        """Load plugins from configuration file."""
        try:
            if not self.config_path.exists():
                logger.warning(f"Plugin config file not found: {self.config_path}")
                return
            
            with open(self.config_path, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
            
            plugins_data = config.get('plugins', [])
            for plugin_data in plugins_data:
                plugin = Plugin(
                    id=plugin_data['id'],
                    name=plugin_data['name'],
                    description=plugin_data['description'],
                    version=plugin_data['version'],
                    capabilities=plugin_data['capabilities'],
                    endpoint=plugin_data['endpoint'],
                    enabled=plugin_data['enabled'],
                    auth_required=plugin_data['auth_required'],
                    max_file_size_mb=plugin_data['max_file_size_mb'],
                    timeout_seconds=plugin_data['timeout_seconds'],
                    rate_limit_per_minute=plugin_data['rate_limit_per_minute'],
                    config=plugin_data.get('config', {})
                )
                self.plugins[plugin.id] = plugin
            
            logger.info(f"Loaded {len(self.plugins)} plugins")
            
        except Exception as e:
            logger.error(f"Error loading plugins: {e}")
            # Continue with empty registry for development
    
    def get_plugin(self, plugin_id: str) -> Optional[Plugin]:
        """Get plugin by ID."""
        return self.plugins.get(plugin_id)
    
    def get_enabled_plugins(self) -> List[Plugin]:
        """Get all enabled plugins."""
        return [plugin for plugin in self.plugins.values() if plugin.enabled]
    
    def get_plugins_by_capability(self, capability: str) -> List[Plugin]:
        """Get plugins that have a specific capability."""
        return [
            plugin for plugin in self.plugins.values()
            if capability in plugin.capabilities and plugin.enabled
        ]
    
    def toggle_plugin(self, plugin_id: str) -> bool:
        """Toggle plugin enabled state."""
        if plugin_id in self.plugins:
            self.plugins[plugin_id].enabled = not self.plugins[plugin_id].enabled
            logger.info(f"Plugin {plugin_id} {'enabled' if self.plugins[plugin_id].enabled else 'disabled'}")
            return True
        return False
    
    def update_plugin_metrics(self, plugin_id: str, metrics: Dict[str, Any]):
        """Update plugin metrics."""
        if plugin_id in self.plugins:
            self.plugins[plugin_id].metrics.update(metrics)
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        total_plugins = len(self.plugins)
        enabled_plugins = len(self.get_enabled_plugins())
        
        capabilities = set()
        for plugin in self.plugins.values():
            capabilities.update(plugin.capabilities)
        
        return {
            "total_plugins": total_plugins,
            "enabled_plugins": enabled_plugins,
            "disabled_plugins": total_plugins - enabled_plugins,
            "available_capabilities": list(capabilities),
            "plugin_list": list(self.plugins.keys())
        }