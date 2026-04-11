import json
import uuid
import time
from typing import Optional, List, Dict, Any
import redis
from app.config import settings
from loguru import logger

class RedisService:
    def __init__(self):
        try:
            self.redis_client = redis.from_url(settings.redis_url, decode_responses=True)
            self.redis_client.ping()
            logger.info(f"Redis connected: {settings.redis_url}")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            self.redis_client = None
    
    def _get_session_key(self, session_id: str) -> str:
        return f"chat:session:{session_id}"
    
    def _get_message_key(self, session_id: str) -> str:
        return f"chat:messages:{session_id}"
    
    def _get_session_list_key(self, user_id: Optional[str] = None) -> str:
        return f"chat:sessions:user:{user_id}" if user_id else "chat:sessions:all"
    
    def create_session(self, user_id: Optional[str] = None, title: Optional[str] = None) -> str:
        if not self.redis_client:
            return str(uuid.uuid4())
        
        session_id = str(uuid.uuid4())
        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "title": title,
            "is_active": True,
            "created_at": str(int(time.time() * 1000)),
            "updated_at": str(int(time.time() * 1000))
        }
        
        session_key = self._get_session_key(session_id)
        self.redis_client.setex(session_key, settings.redis_session_ttl, json.dumps(session_data))
        
        if user_id:
            list_key = self._get_session_list_key(user_id)
            self.redis_client.sadd(list_key, session_id)
            self.redis_client.expire(list_key, settings.redis_session_ttl)
        
        logger.info(f"Session created: {session_id}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        if not self.redis_client:
            return None
        
        session_key = self._get_session_key(session_id)
        session_data = self.redis_client.get(session_key)
        if not session_data:
            return None
        
        try:
            data = json.loads(session_data)
            message_key = self._get_message_key(session_id)
            data["message_count"] = self.redis_client.llen(message_key)
            return data
        except json.JSONDecodeError:
            return None
    
    def delete_session(self, session_id: str) -> bool:
        if not self.redis_client:
            return False
        
        session_key = self._get_session_key(session_id)
        message_key = self._get_message_key(session_id)
        self.redis_client.delete(session_key, message_key)
        
        list_keys = ["chat:sessions:all"]
        session_data = self.get_session(session_id)
        if session_data and session_data.get("user_id"):
            list_keys.append(self._get_session_list_key(session_data["user_id"]))
        
        for list_key in list_keys:
            self.redis_client.srem(list_key, session_id)
        
        logger.info(f"Session deleted: {session_id}")
        return True
    
    def list_sessions(self, user_id: Optional[str] = None, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        if not self.redis_client:
            return []
        
        if user_id and not isinstance(user_id, str):
            user_id = str(user_id)
        
        list_key = self._get_session_list_key(user_id)
        logger.info(f"Listing sessions for user {user_id} with key {list_key}")
        session_ids = self.redis_client.smembers(list_key)
        logger.info(f"Found {len(session_ids)} session IDs: {session_ids}")
        
        sessions = []
        for session_id in session_ids:
            session = self.get_session(session_id)
            if session:
                sessions.append(session)
        
        sessions.sort(key=lambda x: x.get("updated_at", 0), reverse=True)
        logger.info(f"Listed {len(sessions)} sessions for user {user_id}")
        return sessions[offset:offset + limit]
    
    def add_message(self, session_id: str, role: str, content: str, 
                 agent_type: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> None:
        if not self.redis_client:
            return
        
        message = {
            "role": role,
            "content": content,
            "agent_type": agent_type,
            "metadata": metadata,
            "created_at": str(int(time.time() * 1000))
        }
        
        message_key = self._get_message_key(session_id)
        self.redis_client.lpush(message_key, json.dumps(message))
        self.redis_client.expire(message_key, settings.redis_message_ttl)
        
        session_key = self._get_session_key(session_id)
        session_data = self.redis_client.get(session_key)
        if session_data:
            try:
                data = json.loads(session_data)
                data["updated_at"] = str(int(time.time() * 1000))
                self.redis_client.setex(session_key, settings.redis_session_ttl, json.dumps(data))
            except json.JSONDecodeError:
                pass
    
    def get_messages(self, session_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        if not self.redis_client:
            return []
        
        message_key = self._get_message_key(session_id)
        messages = self.redis_client.lrange(message_key, 0, limit - 1)
        
        result = []
        for msg in reversed(messages):
            try:
                result.append(json.loads(msg))
            except json.JSONDecodeError:
                pass
        
        return result

redis_service = RedisService()