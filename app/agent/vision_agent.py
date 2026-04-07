from typing import Dict, Any, Optional, List, List, AsyncGenerator
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from app.config import settings
from loguru import logger

class VisionAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.modelscope_vision_model_id,
            temperature=0.1,
            openai_api_key=settings.modelscope_api_key,
            openai_api_base=settings.modelscope_api_base
        )
    
    async def execute(self, task: str, context: Optional[Dict[str, Any]] = None, images: Optional[List[str]] = None) -> Dict[str, Any]:
        try:
            logger.info(f"VisionAgent processing task: {task[:50]}...")
            
            if not images or not isinstance(images, list) or len(images) == 0:
                return {
                    "success": False,
                    "message": "No image provided",
                    "data": {"input": task, "output": ""},
                    "error": "Image data is required for vision analysis"
                }
            
            # 构建消息内容，包含文本和多个图片
            content = [{"type": "text", "text": task}]
            for image in images:
                content.append({"type": "image_url", "image_url": {"url": image}})
            
            message = HumanMessage(content=content)
            
            response = await self.llm.ainvoke([message])
            
            if not response:
                logger.error("No response from LLM")
                return {
                    "success": False,
                    "message": "No response from model",
                    "data": {"input": task, "output": ""},
                    "error": "Model returned no response"
                }
            
            # 从响应中提取内容
            output = None
            if hasattr(response, 'content'):
                output = response.content
            elif hasattr(response, 'choices') and response.choices:
                for choice in response.choices:
                    if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                        output = choice.message.content
                        break
            
            if not output:
                logger.error(f"Empty output from LLM, response: {response}")
                return {
                    "success": False,
                    "message": "Empty response from model",
                    "data": {"input": task, "output": ""},
                    "error": "Model returned empty content"
                }
            
            logger.info(f"VisionAgent completed successfully")
            
            return {
                "success": True,
                "message": "Image analysis completed",
                "data": {
                    "input": task,
                    "output": output
                },
                "error": None
            }
        except Exception as e:
            error_msg = str(e)
            logger.exception(f"VisionAgent failed: {error_msg}")
            
            if "not support" in error_msg.lower() or "vision" in error_msg.lower():
                error_msg = "当前模型不支持图像分析功能，请使用支持视觉的模型"
            
            return {
                "success": False,
                "message": "Image analysis failed",
                "data": {"input": task, "output": ""},
                "error": error_msg
            }
    
    async def stream_execute(self, task: str, context: Optional[Dict[str, Any]] = None, images: Optional[List[str]] = None) -> AsyncGenerator[str, None]:
        """流式执行图像分析"""
        try:
            logger.info(f"VisionAgent streaming task: {task[:50]}...")
            
            if not images or not isinstance(images, list) or len(images) == 0:
                yield "错误：未提供图片数据"
                return
            
            content = [{"type": "text", "text": task}]
            for image in images:
                content.append({"type": "image_url", "image_url": {"url": image}})
            
            message = HumanMessage(content=content)
            
            async for chunk in self.llm.astream([message]):
                if chunk.content:
                    yield chunk.content
            
            logger.info("VisionAgent streaming completed")
        
        except Exception as e:
            error_msg = str(e)
            logger.exception(f"VisionAgent streaming failed: {error_msg}")
            
            if "not support" in error_msg.lower() or "vision" in error_msg.lower():
                error_msg = "当前模型不支持图像分析功能，请使用支持视觉的模型"
            
            yield f"处理失败: {error_msg}"