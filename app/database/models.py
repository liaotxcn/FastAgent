from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database.connection import Base

class AgentCallHistory(Base):
    """Agent 调用历史表"""
    __tablename__ = "agent_call_history"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_type = Column(String(50), nullable=False, index=True)
    task = Column(Text, nullable=False)
    context = Column(Text, nullable=True)
    tool_name = Column(String(100), nullable=True, index=True)
    tool_input = Column(Text, nullable=True)
    tool_output = Column(Text, nullable=True)
    result = Column(Text, nullable=True)
    success = Column(Integer, nullable=False, default=1)  # 1: 成功, 0: 失败
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    def __repr__(self):
        return f"<AgentCallHistory(id={self.id}, agent_type='{self.agent_type}', created_at='{self.created_at}')>"

class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=False, unique=True, index=True)
    email = Column(String(100), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Integer, nullable=False, default=1)  # 1: 活跃, 0: 禁用
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"

class EmailVerification(Base):
    """邮箱验证码表"""
    __tablename__ = "email_verifications"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), nullable=False, index=True)
    code = Column(String(6), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<EmailVerification(id={self.id}, email='{self.email}', expires_at='{self.expires_at}')>"