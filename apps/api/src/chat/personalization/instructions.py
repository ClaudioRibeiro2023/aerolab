"""
Custom Instructions - Instruções personalizadas por usuário.

Similar ao ChatGPT Custom Instructions.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)


@dataclass
class InstructionProfile:
    """Perfil de instruções customizadas."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Default"
    
    # Instruções
    about_user: str = ""  # "What would you like ChatGPT to know about you?"
    response_style: str = ""  # "How would you like ChatGPT to respond?"
    
    # Contexto adicional
    profession: str = ""
    expertise_areas: List[str] = field(default_factory=list)
    preferred_language: str = "pt-BR"
    
    # Comportamento
    tone: str = "professional"  # professional, casual, technical
    verbosity: str = "balanced"  # concise, balanced, detailed
    code_style: str = "documented"  # minimal, documented, verbose
    
    # Ativo
    is_active: bool = True
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_system_prompt(self) -> str:
        """Converte para prompt de sistema."""
        parts = []
        
        if self.about_user:
            parts.append(f"About the user: {self.about_user}")
        
        if self.profession:
            parts.append(f"User's profession: {self.profession}")
        
        if self.expertise_areas:
            parts.append(f"Areas of expertise: {', '.join(self.expertise_areas)}")
        
        if self.response_style:
            parts.append(f"Response preferences: {self.response_style}")
        
        parts.append(f"Preferred tone: {self.tone}")
        parts.append(f"Verbosity level: {self.verbosity}")
        parts.append(f"Preferred language: {self.preferred_language}")
        
        return "\n".join(parts)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "about_user": self.about_user,
            "response_style": self.response_style,
            "profession": self.profession,
            "expertise_areas": self.expertise_areas,
            "preferred_language": self.preferred_language,
            "tone": self.tone,
            "verbosity": self.verbosity,
            "code_style": self.code_style,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class CustomInstructions:
    """
    Gerenciador de instruções customizadas.
    """
    
    def __init__(self):
        self._profiles: Dict[str, Dict[str, InstructionProfile]] = {}  # user_id -> {profile_id -> profile}
        self._active_profiles: Dict[str, str] = {}  # user_id -> active_profile_id
    
    async def get_profile(
        self,
        user_id: str,
        profile_id: Optional[str] = None
    ) -> Optional[InstructionProfile]:
        """Obtém perfil de instruções."""
        if user_id not in self._profiles:
            return None
        
        if profile_id:
            return self._profiles[user_id].get(profile_id)
        
        # Retorna o perfil ativo
        active_id = self._active_profiles.get(user_id)
        if active_id and active_id in self._profiles[user_id]:
            return self._profiles[user_id][active_id]
        
        # Retorna o primeiro
        profiles = list(self._profiles[user_id].values())
        return profiles[0] if profiles else None
    
    async def create_profile(
        self,
        user_id: str,
        name: str = "Default",
        **kwargs
    ) -> InstructionProfile:
        """Cria novo perfil."""
        profile = InstructionProfile(name=name, **kwargs)
        
        if user_id not in self._profiles:
            self._profiles[user_id] = {}
        
        self._profiles[user_id][profile.id] = profile
        
        # Se é o primeiro, marca como ativo
        if user_id not in self._active_profiles:
            self._active_profiles[user_id] = profile.id
        
        logger.info(f"Created instruction profile {profile.id} for user {user_id}")
        return profile
    
    async def update_profile(
        self,
        user_id: str,
        profile_id: str,
        **kwargs
    ) -> Optional[InstructionProfile]:
        """Atualiza perfil."""
        if user_id not in self._profiles:
            return None
        
        profile = self._profiles[user_id].get(profile_id)
        if not profile:
            return None
        
        for key, value in kwargs.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        
        profile.updated_at = datetime.now()
        return profile
    
    async def delete_profile(
        self,
        user_id: str,
        profile_id: str
    ) -> bool:
        """Deleta perfil."""
        if user_id not in self._profiles:
            return False
        
        if profile_id in self._profiles[user_id]:
            del self._profiles[user_id][profile_id]
            
            # Se era o ativo, limpa
            if self._active_profiles.get(user_id) == profile_id:
                del self._active_profiles[user_id]
            
            return True
        return False
    
    async def set_active_profile(
        self,
        user_id: str,
        profile_id: str
    ) -> bool:
        """Define perfil ativo."""
        if user_id in self._profiles and profile_id in self._profiles[user_id]:
            self._active_profiles[user_id] = profile_id
            return True
        return False
    
    async def list_profiles(self, user_id: str) -> List[InstructionProfile]:
        """Lista todos os perfis do usuário."""
        if user_id not in self._profiles:
            return []
        return list(self._profiles[user_id].values())
    
    async def get_system_prompt(self, user_id: str) -> str:
        """Obtém system prompt baseado no perfil ativo."""
        profile = await self.get_profile(user_id)
        if profile:
            return profile.to_system_prompt()
        return ""


# Singleton
_custom_instructions: Optional[CustomInstructions] = None


def get_custom_instructions() -> CustomInstructions:
    global _custom_instructions
    if _custom_instructions is None:
        _custom_instructions = CustomInstructions()
    return _custom_instructions
