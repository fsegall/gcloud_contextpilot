"""
Base Agent Class

Provides common functionality for all agents:
- Event publishing and subscription
- State persistence (Firestore or JSON)
- Artifact consumption with rules
- Logging and error handling
"""

import os
import json
import logging
import yaml
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

from app.services.event_bus import get_event_bus, EventBusInterface
from app.utils.workspace_manager import get_workspace_path

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Base class for all ContextPilot agents.
    
    Provides:
    - Event publishing/subscription
    - Persistent state management
    - Artifact consumption with rules
    - Workspace path resolution
    """
    
    def __init__(self, workspace_id: str, agent_id: str, project_id: Optional[str] = None):
        """
        Initialize base agent.
        
        Args:
            workspace_id: Workspace identifier
            agent_id: Agent identifier (e.g., 'spec', 'git', 'strategy')
            project_id: GCP project ID (for Pub/Sub)
        """
        self.workspace_id = workspace_id
        self.agent_id = agent_id
        self.project_id = project_id or os.getenv('GCP_PROJECT_ID')
        
        # Get workspace path
        self.workspace_path = get_workspace_path(workspace_id)
        
        # Initialize event bus
        self.event_bus = get_event_bus(
            project_id=self.project_id,
            force_in_memory=os.getenv('USE_PUBSUB', 'false').lower() != 'true'
        )
        
        # Load agent state
        self.state = self._load_state()
        
        # Load artifact configuration
        self.artifacts_config = self._load_artifacts_config()
        self.agent_rules = self._get_my_rules()
        
        logger.info(f"[{self.agent_id}] Initialized for workspace: {workspace_id}")
        if self.agent_rules:
            logger.info(f"[{self.agent_id}] Loaded {len(self.agent_rules)} artifact rules")
    
    # ========== State Management ==========
    
    def _get_state_path(self) -> Path:
        """Get path to agent state file"""
        state_dir = Path(self.workspace_path) / '.agent_state'
        state_dir.mkdir(exist_ok=True)
        return state_dir / f"{self.agent_id}_state.json"
    
    def _load_state(self) -> Dict[str, Any]:
        """Load agent state from JSON file"""
        state_path = self._get_state_path()
        
        if state_path.exists():
            try:
                with open(state_path, 'r') as f:
                    state = json.load(f)
                logger.info(f"[{self.agent_id}] Loaded state from {state_path}")
                return state
            except Exception as e:
                logger.error(f"[{self.agent_id}] Failed to load state: {e}")
                return self._default_state()
        else:
            logger.info(f"[{self.agent_id}] No existing state, using defaults")
            return self._default_state()
    
    def _default_state(self) -> Dict[str, Any]:
        """Get default state structure"""
        return {
            'agent_id': self.agent_id,
            'workspace_id': self.workspace_id,
            'created_at': datetime.utcnow().isoformat(),
            'last_updated': datetime.utcnow().isoformat(),
            'memory': {},
            'metrics': {
                'events_processed': 0,
                'events_published': 0,
                'errors': 0
            }
        }
    
    def _save_state(self) -> None:
        """Persist agent state to JSON file"""
        state_path = self._get_state_path()
        
        # Update timestamp
        self.state['last_updated'] = datetime.utcnow().isoformat()
        
        try:
            with open(state_path, 'w') as f:
                json.dump(self.state, f, indent=2)
            logger.debug(f"[{self.agent_id}] Saved state to {state_path}")
        except Exception as e:
            logger.error(f"[{self.agent_id}] Failed to save state: {e}")
    
    def remember(self, key: str, value: Any) -> None:
        """
        Store value in agent memory.
        
        Args:
            key: Memory key
            value: Value to store (must be JSON-serializable)
        """
        if 'memory' not in self.state:
            self.state['memory'] = {}
        
        self.state['memory'][key] = value
        self._save_state()
        logger.debug(f"[{self.agent_id}] Remembered: {key}")
    
    def recall(self, key: str, default: Any = None) -> Any:
        """
        Retrieve value from agent memory.
        
        Args:
            key: Memory key
            default: Default value if key not found
        
        Returns:
            Stored value or default
        """
        return self.state.get('memory', {}).get(key, default)
    
    def forget(self, key: str) -> None:
        """Remove value from agent memory"""
        if 'memory' in self.state and key in self.state['memory']:
            del self.state['memory'][key]
            self._save_state()
            logger.debug(f"[{self.agent_id}] Forgot: {key}")
    
    # ========== Event Handling ==========
    
    async def publish_event(self, topic: str, event_type: str, data: Dict) -> str:
        """
        Publish event to event bus.
        
        Args:
            topic: Pub/Sub topic name
            event_type: Event type (e.g., 'proposal.created.v1')
            data: Event data payload
        
        Returns:
            Event ID or message ID
        """
        try:
            event_id = await self.event_bus.publish(
                topic=topic,
                event_type=event_type,
                source=self.agent_id,
                data=data
            )
            
            # Update metrics
            self.state['metrics']['events_published'] += 1
            self._save_state()
            
            logger.info(f"[{self.agent_id}] Published {event_type} to {topic}")
            return event_id
        except Exception as e:
            logger.error(f"[{self.agent_id}] Failed to publish event: {e}")
            self.state['metrics']['errors'] += 1
            self._save_state()
            raise
    
    def subscribe_to_event(self, event_type: str) -> None:
        """
        Subscribe to event type.
        
        Args:
            event_type: Event type to subscribe to
        """
        self.event_bus.subscribe(event_type, self.handle_event)
        logger.info(f"[{self.agent_id}] Subscribed to {event_type}")
    
    @abstractmethod
    async def handle_event(self, event_type: str, data: Dict) -> None:
        """
        Handle incoming event.
        Must be implemented by subclasses.
        
        Args:
            event_type: Type of event
            data: Event data payload
        """
        pass
    
    # ========== Artifact Management ==========
    
    def _load_artifacts_config(self) -> Dict:
        """Load artifacts.yaml configuration"""
        config_path = Path(self.workspace_path) / 'artifacts.yaml'
        
        if not config_path.exists():
            # Try to copy from template
            template_path = Path(__file__).parent.parent / 'templates' / 'artifacts.yaml'
            if template_path.exists():
                import shutil
                shutil.copy(template_path, config_path)
                logger.info(f"[{self.agent_id}] Created artifacts.yaml from template")
        
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                return config or {}
            except Exception as e:
                logger.error(f"[{self.agent_id}] Failed to load artifacts.yaml: {e}")
                return {}
        else:
            logger.warning(f"[{self.agent_id}] No artifacts.yaml found")
            return {}
    
    def _get_my_rules(self) -> Dict[str, str]:
        """Get all artifact rules that apply to this agent"""
        rules = {}
        
        # Check custom artifacts
        for artifact_name, config in self.artifacts_config.get('custom_artifacts', {}).items():
            consumers = config.get('consumers', [])
            if self.agent_id in consumers:
                agent_rules = config.get('agent_rules', {})
                if self.agent_id in agent_rules:
                    rules[artifact_name] = agent_rules[self.agent_id]
        
        # Check system artifacts
        for artifact_name, config in self.artifacts_config.get('system_artifacts', {}).items():
            consumers = config.get('consumers', [])
            if self.agent_id in consumers:
                agent_rules = config.get('agent_rules', {})
                if self.agent_id in agent_rules:
                    rules[artifact_name] = agent_rules[self.agent_id]
        
        return rules
    
    def consume_artifact(self, artifact_name: str) -> str:
        """
        Read artifact content.
        
        Args:
            artifact_name: Name of artifact file
        
        Returns:
            Artifact content as string
        """
        artifact_path = Path(self.workspace_path) / artifact_name
        
        if not artifact_path.exists():
            logger.warning(f"[{self.agent_id}] Artifact not found: {artifact_name}")
            return ""
        
        try:
            with open(artifact_path, 'r') as f:
                content = f.read()
            
            # Log consumption
            rule = self.agent_rules.get(artifact_name)
            logger.info(f"[{self.agent_id}] Reading {artifact_name}")
            if rule:
                logger.debug(f"[{self.agent_id}] Applying rule: {rule[:100]}...")
            
            return content
        except Exception as e:
            logger.error(f"[{self.agent_id}] Failed to read {artifact_name}: {e}")
            return ""
    
    def get_artifact_rule(self, artifact_name: str) -> Optional[str]:
        """Get the rule for a specific artifact"""
        return self.agent_rules.get(artifact_name)
    
    def apply_artifact_rules(self, context: Dict) -> Dict:
        """
        Apply artifact rules to decision-making context.
        Injects rules into LLM prompt context.
        
        Args:
            context: Current decision context
        
        Returns:
            Context with artifact rules injected
        """
        if not self.agent_rules:
            return context
        
        context['artifact_rules'] = context.get('artifact_rules', [])
        
        for artifact_name, rule in self.agent_rules.items():
            # Read artifact content
            content = self.consume_artifact(artifact_name)
            
            context['artifact_rules'].append({
                'artifact': artifact_name,
                'rule': rule,
                'content': content
            })
        
        return context
    
    # ========== Utility Methods ==========
    
    def get_workspace_file_path(self, filename: str) -> Path:
        """Get full path to file in workspace"""
        return Path(self.workspace_path) / filename
    
    def log_metric(self, metric_name: str, value: Any) -> None:
        """Log a metric to agent state"""
        if 'metrics' not in self.state:
            self.state['metrics'] = {}
        
        self.state['metrics'][metric_name] = value
        self._save_state()
    
    def increment_metric(self, metric_name: str, amount: int = 1) -> None:
        """Increment a numeric metric"""
        if 'metrics' not in self.state:
            self.state['metrics'] = {}
        
        current = self.state['metrics'].get(metric_name, 0)
        self.state['metrics'][metric_name] = current + amount
        self._save_state()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all agent metrics"""
        return self.state.get('metrics', {})
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} agent_id={self.agent_id} workspace={self.workspace_id}>"

