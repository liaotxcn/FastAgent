from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.database.models import User, EmailVerification
from app.config import settings
from loguru import logger

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    """用户认证服务"""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """获取密码哈希值"""
        return pwd_context.hash(password)
    
    @staticmethod
    def generate_email_code() -> str:
        """生成6位数字验证码"""
        return ''.join(secrets.choice('0123456789') for _ in range(6))
    
    @staticmethod
    async def send_email_code(email: str, code: str) -> bool:
        """发送邮箱验证码"""
        try:
            msg = MIMEMultipart()
            msg['From'] = settings.email_from
            msg['To'] = email
            msg['Subject'] = "FastAgent 登录验证码"
            
            body = f"您的登录验证码是：{code}，有效期为5分钟。请勿向他人泄露此验证码。"
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # 启用SMTP发送
            with smtplib.SMTP(settings.smtp_server, settings.smtp_port) as server:
                server.starttls()
                server.login(settings.smtp_username, settings.smtp_password)
                server.send_message(msg)
            
            logger.info(f"验证码 {code} 已发送至邮箱 {email}")
            return True
        except Exception as e:
            logger.error(f"发送验证码失败: {e}")
            return False
    
    @staticmethod
    async def create_email_verification(db: AsyncSession, email: str) -> str:
        """创建邮箱验证码"""
        # 生成验证码
        code = AuthService.generate_email_code()
        
        # 设置过期时间为5分钟
        expires_at = datetime.utcnow() + timedelta(minutes=5)
        
        # 先删除该邮箱的旧验证码
        await db.execute(
            select(EmailVerification).where(EmailVerification.email == email)
        )
        
        # 创建新验证码
        verification = EmailVerification(
            email=email,
            code=code,
            expires_at=expires_at
        )
        
        db.add(verification)
        await db.commit()
        await db.refresh(verification)
        
        # 发送验证码
        await AuthService.send_email_code(email, code)
        
        return code
    
    @staticmethod
    async def verify_email_code(db: AsyncSession, email: str, code: str) -> bool:
        """验证邮箱验证码"""
        # 查询验证码
        result = await db.execute(
            select(EmailVerification).where(
                EmailVerification.email == email,
                EmailVerification.code == code,
                EmailVerification.expires_at > datetime.utcnow()
            )
        )
        
        verification = result.scalars().first()
        
        if verification:
            # 验证成功后删除验证码
            await db.delete(verification)
            await db.commit()
            return True
        
        return False
    
    @staticmethod
    async def register(db: AsyncSession, username: str, password: str, email: str) -> Dict[str, Any]:
        """用户注册"""
        try:
            # 检查用户名是否已存在
            result = await db.execute(
                select(User).where(User.username == username)
            )
            if result.scalars().first():
                return {
                    "success": False,
                    "message": "用户名已存在",
                    "error": "Username already exists"
                }
            
            # 检查邮箱是否已存在
            result = await db.execute(
                select(User).where(User.email == email)
            )
            if result.scalars().first():
                return {
                    "success": False,
                    "message": "邮箱已被注册",
                    "error": "Email already registered"
                }
            
            # 创建新用户
            hashed_password = AuthService.get_password_hash(password)
            user = User(
                username=username,
                email=email,
                password_hash=hashed_password
            )
            
            db.add(user)
            await db.commit()
            await db.refresh(user)
            
            return {
                "success": True,
                "message": "注册成功",
                "data": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email
                }
            }
        except IntegrityError:
            await db.rollback()
            return {
                "success": False,
                "message": "注册失败，数据已存在",
                "error": "Data integrity error"
            }
        except Exception as e:
            await db.rollback()
            logger.error(f"注册失败: {e}")
            return {
                "success": False,
                "message": "注册失败，请稍后重试",
                "error": str(e)
            }
    
    @staticmethod
    async def login(db: AsyncSession, username: str, password: str, email_code: str) -> Dict[str, Any]:
        """用户登录"""
        try:
            # 查找用户
            result = await db.execute(
                select(User).where(User.username == username)
            )
            user = result.scalars().first()
            
            if not user:
                return {
                    "success": False,
                    "message": "用户名或密码错误",
                    "error": "Invalid username or password"
                }
            
            # 验证密码
            if not AuthService.verify_password(password, user.password_hash):
                return {
                    "success": False,
                    "message": "用户名或密码错误",
                    "error": "Invalid username or password"
                }
            
            # 验证邮箱验证码
            if not await AuthService.verify_email_code(db, user.email, email_code):
                return {
                    "success": False,
                    "message": "邮箱验证码错误或已过期",
                    "error": "Invalid or expired email code"
                }
            
            return {
                "success": True,
                "message": "登录成功",
                "data": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email
                }
            }
        except Exception as e:
            logger.error(f"登录失败: {e}")
            return {
                "success": False,
                "message": "登录失败，请稍后重试",
                "error": str(e)
            }

# 创建认证服务实例
auth_service = AuthService()