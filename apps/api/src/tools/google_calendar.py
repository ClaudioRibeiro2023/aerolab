"""
Ferramenta de integração com Google Calendar.

Permite criar eventos, listar agendamentos e gerenciar calendários.
"""

import os
import json
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import httpx

from .base import BaseTool


class GoogleCalendarTool(BaseTool):
    """
    Ferramenta para integração com Google Calendar API.
    
    Funcionalidades:
    - Criar eventos
    - Listar eventos
    - Atualizar eventos
    - Deletar eventos
    - Buscar horários livres
    
    Configuração:
        Requer GOOGLE_CALENDAR_CLIENT_ID, GOOGLE_CALENDAR_CLIENT_SECRET,
        e GOOGLE_CALENDAR_REFRESH_TOKEN.
    """
    
    name = "google_calendar"
    description = "Gerencia eventos e calendários no Google Calendar"
    
    def __init__(
        self,
        credentials: Optional[Dict[str, str]] = None,
        default_calendar: str = "primary"
    ):
        self.base_url = "https://www.googleapis.com/calendar/v3"
        self.default_calendar = default_calendar
        
        if credentials:
            self.credentials = credentials
        else:
            self.credentials = {
                "client_id": os.getenv("GOOGLE_CALENDAR_CLIENT_ID") or os.getenv("GMAIL_CLIENT_ID"),
                "client_secret": os.getenv("GOOGLE_CALENDAR_CLIENT_SECRET") or os.getenv("GMAIL_CLIENT_SECRET"),
                "refresh_token": os.getenv("GOOGLE_CALENDAR_REFRESH_TOKEN") or os.getenv("GMAIL_REFRESH_TOKEN"),
            }
        
        self._access_token: Optional[str] = None
    
    async def _get_access_token(self) -> str:
        """Obtém ou renova o access token."""
        if self._access_token:
            return self._access_token
        
        if not all([self.credentials.get("client_id"), 
                    self.credentials.get("client_secret"),
                    self.credentials.get("refresh_token")]):
            raise ValueError(
                "Google Calendar credentials não configuradas."
            )
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": self.credentials["client_id"],
                    "client_secret": self.credentials["client_secret"],
                    "refresh_token": self.credentials["refresh_token"],
                    "grant_type": "refresh_token",
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to refresh token: {response.text}")
            
            data = response.json()
            self._access_token = data["access_token"]
            return self._access_token
    
    def _headers(self, token: str) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Faz uma requisição à API do Google Calendar."""
        token = await self._get_access_token()
        
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method,
                f"{self.base_url}/{endpoint}",
                headers=self._headers(token),
                **kwargs
            )
            
            if response.status_code >= 400:
                raise Exception(f"Google Calendar API error: {response.status_code} - {response.text}")
            
            return response.json() if response.text else {}
    
    async def create_event(
        self,
        summary: str,
        start: str,
        end: str,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[List[str]] = None,
        reminders: Optional[List[Dict[str, Any]]] = None,
        calendar_id: Optional[str] = None,
        timezone: str = "America/Sao_Paulo"
    ) -> Dict[str, Any]:
        """
        Cria um evento no calendário.
        
        Args:
            summary: Título do evento
            start: Data/hora início (ISO 8601 ou "YYYY-MM-DD HH:MM")
            end: Data/hora fim
            description: Descrição do evento
            location: Local
            attendees: Lista de emails de participantes
            reminders: Lembretes personalizados
            calendar_id: ID do calendário
            timezone: Fuso horário
        
        Returns:
            Dados do evento criado
        """
        # Normalizar datas
        start_dt = self._parse_datetime(start, timezone)
        end_dt = self._parse_datetime(end, timezone)
        
        event = {
            "summary": summary,
            "start": start_dt,
            "end": end_dt,
        }
        
        if description:
            event["description"] = description
        if location:
            event["location"] = location
        if attendees:
            event["attendees"] = [{"email": email} for email in attendees]
        if reminders:
            event["reminders"] = {
                "useDefault": False,
                "overrides": reminders
            }
        
        cal_id = calendar_id or self.default_calendar
        return await self._request(
            "POST",
            f"calendars/{cal_id}/events",
            json=event
        )
    
    async def create_quick_event(
        self,
        text: str,
        calendar_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cria evento usando linguagem natural.
        
        Args:
            text: Descrição em linguagem natural (ex: "Reunião amanhã às 15h")
            calendar_id: ID do calendário
        
        Returns:
            Dados do evento criado
        """
        cal_id = calendar_id or self.default_calendar
        return await self._request(
            "POST",
            f"calendars/{cal_id}/events/quickAdd",
            params={"text": text}
        )
    
    async def list_events(
        self,
        time_min: Optional[str] = None,
        time_max: Optional[str] = None,
        max_results: int = 10,
        calendar_id: Optional[str] = None,
        query: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Lista eventos do calendário.
        
        Args:
            time_min: Data mínima (default: agora)
            time_max: Data máxima
            max_results: Número máximo de resultados
            calendar_id: ID do calendário
            query: Texto para buscar
        
        Returns:
            Lista de eventos
        """
        params: Dict[str, Any] = {
            "maxResults": max_results,
            "singleEvents": True,
            "orderBy": "startTime",
        }
        
        if time_min:
            params["timeMin"] = self._to_rfc3339(time_min)
        else:
            params["timeMin"] = datetime.utcnow().isoformat() + "Z"
        
        if time_max:
            params["timeMax"] = self._to_rfc3339(time_max)
        
        if query:
            params["q"] = query
        
        cal_id = calendar_id or self.default_calendar
        data = await self._request("GET", f"calendars/{cal_id}/events", params=params)
        return data.get("items", [])
    
    async def get_event(
        self,
        event_id: str,
        calendar_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Obtém detalhes de um evento."""
        cal_id = calendar_id or self.default_calendar
        return await self._request("GET", f"calendars/{cal_id}/events/{event_id}")
    
    async def update_event(
        self,
        event_id: str,
        calendar_id: Optional[str] = None,
        **updates
    ) -> Dict[str, Any]:
        """
        Atualiza um evento.
        
        Args:
            event_id: ID do evento
            calendar_id: ID do calendário
            **updates: Campos a atualizar (summary, description, start, end, etc.)
        """
        cal_id = calendar_id or self.default_calendar
        
        # Obter evento atual
        event = await self.get_event(event_id, cal_id)
        
        # Aplicar atualizações
        for key, value in updates.items():
            if key in ["start", "end"]:
                event[key] = self._parse_datetime(value, "America/Sao_Paulo")
            else:
                event[key] = value
        
        return await self._request(
            "PUT",
            f"calendars/{cal_id}/events/{event_id}",
            json=event
        )
    
    async def delete_event(
        self,
        event_id: str,
        calendar_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Deleta um evento."""
        cal_id = calendar_id or self.default_calendar
        await self._request("DELETE", f"calendars/{cal_id}/events/{event_id}")
        return {"deleted": event_id}
    
    async def list_calendars(self) -> List[Dict[str, Any]]:
        """Lista calendários disponíveis."""
        data = await self._request("GET", "users/me/calendarList")
        return data.get("items", [])
    
    async def find_free_slots(
        self,
        duration_minutes: int = 60,
        days_ahead: int = 7,
        working_hours: tuple = (9, 18),
        calendar_id: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        Encontra horários livres.
        
        Args:
            duration_minutes: Duração desejada em minutos
            days_ahead: Quantos dias à frente buscar
            working_hours: Horário de trabalho (início, fim)
            calendar_id: ID do calendário
        
        Returns:
            Lista de slots livres
        """
        now = datetime.now()
        end_date = now + timedelta(days=days_ahead)
        
        # Buscar eventos existentes
        events = await self.list_events(
            time_min=now.isoformat(),
            time_max=end_date.isoformat(),
            max_results=100,
            calendar_id=calendar_id
        )
        
        # Extrair períodos ocupados
        busy_periods = []
        for event in events:
            start = event.get("start", {}).get("dateTime")
            end = event.get("end", {}).get("dateTime")
            if start and end:
                busy_periods.append((
                    datetime.fromisoformat(start.replace("Z", "+00:00")),
                    datetime.fromisoformat(end.replace("Z", "+00:00"))
                ))
        
        # Encontrar slots livres
        free_slots = []
        current = now
        
        while current < end_date:
            # Pular para horário de trabalho
            if current.hour < working_hours[0]:
                current = current.replace(hour=working_hours[0], minute=0)
            elif current.hour >= working_hours[1]:
                current = (current + timedelta(days=1)).replace(hour=working_hours[0], minute=0)
                continue
            
            # Pular fim de semana
            if current.weekday() >= 5:
                current = current + timedelta(days=1)
                continue
            
            slot_end = current + timedelta(minutes=duration_minutes)
            
            # Verificar se slot está livre
            is_free = True
            for busy_start, busy_end in busy_periods:
                if not (slot_end <= busy_start or current >= busy_end):
                    is_free = False
                    current = busy_end
                    break
            
            if is_free:
                free_slots.append({
                    "start": current.isoformat(),
                    "end": slot_end.isoformat()
                })
                current = slot_end
            
            if len(free_slots) >= 10:
                break
        
        return free_slots
    
    def _parse_datetime(self, dt_str: str, timezone: str) -> Dict[str, str]:
        """Converte string para formato de datetime do Calendar API."""
        try:
            # Tentar ISO 8601
            if "T" in dt_str:
                return {"dateTime": dt_str, "timeZone": timezone}
            # Formato simples
            dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
            return {"dateTime": dt.isoformat(), "timeZone": timezone}
        except ValueError:
            # Só data
            return {"date": dt_str}
    
    def _to_rfc3339(self, dt_str: str) -> str:
        """Converte para formato RFC 3339."""
        if "T" in dt_str and "Z" not in dt_str and "+" not in dt_str:
            return dt_str + "Z"
        return dt_str
    
    def run(self, action: str, **kwargs) -> str:
        """
        Executa uma ação do Google Calendar.
        
        Args:
            action: Ação (create, quick_create, list, get, update, delete, calendars, free_slots)
            **kwargs: Argumentos da ação
        """
        import asyncio
        
        actions = {
            "create": self.create_event,
            "quick_create": self.create_quick_event,
            "list": self.list_events,
            "get": self.get_event,
            "update": self.update_event,
            "delete": self.delete_event,
            "calendars": self.list_calendars,
            "free_slots": self.find_free_slots,
        }
        
        if action not in actions:
            return f"Ação desconhecida: {action}. Disponíveis: {list(actions.keys())}"
        
        result = asyncio.run(actions[action](**kwargs))
        return json.dumps(result, indent=2, default=str)


def get_google_calendar_tool() -> GoogleCalendarTool:
    """Factory para criar GoogleCalendarTool."""
    return GoogleCalendarTool()
