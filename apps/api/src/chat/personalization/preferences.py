"""
User Preferences - Preferências de UI e comportamento.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class UserPreferences:
    """Preferências do usuário."""
    user_id: str = ""
    
    # UI
    theme: str = "system"  # light, dark, system
    font_size: str = "medium"  # small, medium, large
    compact_mode: bool = False
    show_timestamps: bool = True
    
    # Chat
    default_model: str = "gpt-4o"
    default_agent_id: Optional[str] = None
    auto_scroll: bool = True
    enter_to_send: bool = True
    
    # Features
    enable_voice_mode: bool = False
    enable_web_search: bool = False
    enable_code_execution: bool = False
    enable_reasoning_display: bool = False
    
    # Notifications
    enable_notifications: bool = True
    notification_sound: bool = True
    
    # Privacy
    save_history: bool = True
    share_analytics: bool = False
    
    # Timestamps
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "user_id": self.user_id,
            "theme": self.theme,
            "font_size": self.font_size,
            "compact_mode": self.compact_mode,
            "show_timestamps": self.show_timestamps,
            "default_model": self.default_model,
            "default_agent_id": self.default_agent_id,
            "auto_scroll": self.auto_scroll,
            "enter_to_send": self.enter_to_send,
            "enable_voice_mode": self.enable_voice_mode,
            "enable_web_search": self.enable_web_search,
            "enable_code_execution": self.enable_code_execution,
            "enable_reasoning_display": self.enable_reasoning_display,
            "enable_notifications": self.enable_notifications,
            "notification_sound": self.notification_sound,
            "save_history": self.save_history,
            "share_analytics": self.share_analytics,
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "UserPreferences":
        return cls(
            user_id=data.get("user_id", ""),
            theme=data.get("theme", "system"),
            font_size=data.get("font_size", "medium"),
            compact_mode=data.get("compact_mode", False),
            show_timestamps=data.get("show_timestamps", True),
            default_model=data.get("default_model", "gpt-4o"),
            default_agent_id=data.get("default_agent_id"),
            auto_scroll=data.get("auto_scroll", True),
            enter_to_send=data.get("enter_to_send", True),
            enable_voice_mode=data.get("enable_voice_mode", False),
            enable_web_search=data.get("enable_web_search", False),
            enable_code_execution=data.get("enable_code_execution", False),
            enable_reasoning_display=data.get("enable_reasoning_display", False),
            enable_notifications=data.get("enable_notifications", True),
            notification_sound=data.get("notification_sound", True),
            save_history=data.get("save_history", True),
            share_analytics=data.get("share_analytics", False)
        )


class PreferencesManager:
    """Gerenciador de preferências."""
    
    def __init__(self):
        self._preferences: Dict[str, UserPreferences] = {}
    
    async def get(self, user_id: str) -> UserPreferences:
        """Obtém preferências do usuário."""
        if user_id not in self._preferences:
            self._preferences[user_id] = UserPreferences(user_id=user_id)
        return self._preferences[user_id]
    
    async def update(
        self,
        user_id: str,
        **kwargs
    ) -> UserPreferences:
        """Atualiza preferências."""
        prefs = await self.get(user_id)
        
        for key, value in kwargs.items():
            if hasattr(prefs, key):
                setattr(prefs, key, value)
        
        prefs.updated_at = datetime.now()
        return prefs
    
    async def reset(self, user_id: str) -> UserPreferences:
        """Reseta para padrões."""
        self._preferences[user_id] = UserPreferences(user_id=user_id)
        return self._preferences[user_id]


# Singleton
_preferences_manager: Optional[PreferencesManager] = None


def get_preferences_manager() -> PreferencesManager:
    global _preferences_manager
    if _preferences_manager is None:
        _preferences_manager = PreferencesManager()
    return _preferences_manager
