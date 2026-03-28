from typing import Optional, List
from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import ChatSession, ChatMessage
from app.database.connection import AsyncSessionLocal
from loguru import logger
import uuid
import json

class ChatService:
    @staticmethod
    async def create_session(user_id: Optional[str] = None, title: Optional[str] = None) -> str:
        session_id = str(uuid.uuid4())
        async with AsyncSessionLocal() as session:
            chat_session = ChatSession(
                session_id=session_id,
                user_id=user_id,
                title=title
            )
            session.add(chat_session)
            await session.commit()
        logger.info(f"Created session: {session_id}")
        return session_id
    
    @staticmethod
    async def get_session(session_id: str) -> Optional[dict]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(ChatSession).where(ChatSession.session_id == session_id)
            )
            chat_session = result.scalar_one_or_none()
            if not chat_session:
                return None
            
            message_count = await session.scalar(
                select(func.count(ChatMessage.id)).where(ChatMessage.session_id == session_id)
            )
            
            return {
                "session_id": chat_session.session_id,
                "user_id": chat_session.user_id,
                "title": chat_session.title,
                "is_active": chat_session.is_active,
                "created_at": chat_session.created_at,
                "updated_at": chat_session.updated_at,
                "message_count": message_count
            }
    
    @staticmethod
    async def delete_session(session_id: str) -> bool:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                delete(ChatSession).where(ChatSession.session_id == session_id)
            )
            await session.commit()
            deleted = result.rowcount > 0
            if deleted:
                logger.info(f"Deleted session: {session_id}")
            return deleted
    
    @staticmethod
    async def list_sessions(user_id: Optional[str] = None, is_active: Optional[bool] = None, 
                           limit: int = 20, offset: int = 0) -> List[dict]:
        async with AsyncSessionLocal() as session:
            query = select(ChatSession)
            
            if user_id:
                query = query.where(ChatSession.user_id == user_id)
            if is_active is not None:
                query = query.where(ChatSession.is_active == is_active)
            
            query = query.order_by(ChatSession.updated_at.desc()).limit(limit).offset(offset)
            
            result = await session.execute(query)
            sessions = result.scalars().all()
            
            session_list = []
            for s in sessions:
                message_count = await session.scalar(
                    select(func.count(ChatMessage.id)).where(ChatMessage.session_id == s.session_id)
                )
                session_list.append({
                    "session_id": s.session_id,
                    "user_id": s.user_id,
                    "title": s.title,
                    "is_active": s.is_active,
                    "created_at": s.created_at,
                    "updated_at": s.updated_at,
                    "message_count": message_count
                })
            return session_list
    
    @staticmethod
    async def add_message(session_id: str, role: str, content: str, 
                         agent_type: Optional[str] = None, metadata: Optional[dict] = None) -> int:
        async with AsyncSessionLocal() as session:
            message = ChatMessage(
                session_id=session_id,
                role=role,
                content=content,
                agent_type=agent_type,
                msg_metadata=json.dumps(metadata) if metadata else None
            )
            session.add(message)
            await session.commit()
            await session.refresh(message)
            return message.id
    
    @staticmethod
    async def get_messages(session_id: str, limit: int = 100) -> List[dict]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(ChatMessage)
                .where(ChatMessage.session_id == session_id)
                .order_by(ChatMessage.created_at.asc())
                .limit(limit)
            )
            messages = result.scalars().all()
            return [
                {
                    "id": m.id,
                    "role": m.role,
                    "content": m.content,
                    "agent_type": m.agent_type,
                    "metadata": json.loads(m.msg_metadata) if m.msg_metadata else None,
                    "created_at": m.created_at
                }
                for m in messages
            ]