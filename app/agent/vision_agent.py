from typing import Dict, Any, Optional
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
    
    async def execute(self, task: str, context: Optional[Dict[str, Any]] = None, image: Optional[str] = None) -> Dict[str, Any]:
        try:
            logger.info(f"VisionAgent processing task: {task[:50]}...")
            
            if not image:
                return {
                    "success": False,
                    "message": "No image provided",
                    "data": {"input": task, "output": ""},
                    "error": "Image data is required for vision analysis"
                }
            
            message = HumanMessage(
                content=[
                    {"type": "text", "text": task},
                    {"type": "image_url", "image_url": {"url": image}}
                ]
            )
            
            response = await self.llm.ainvoke([message])
            
            if not response:
                logger.error("No response from LLM")
                return {
                    "success": False,
                    "message": "No response from model",
                    "data": {"input": task, "output": ""},
                    "error": "Model returned no response"
                }
            
            output = response.content if hasattr(response, 'content') else str(response)
            
            if not output:
                logger.error("Empty output from LLM")
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