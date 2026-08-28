from typing import Dict, Any, Optional, List, AsyncGenerator
from langchain_core.messages import HumanMessage
from app.agent.base import BaseAgent
from app.config import settings
from loguru import logger


class VisionAgent(BaseAgent):
    def __init__(self, model_name=None, temperature=None):
        super().__init__(
            model_name=model_name or settings.modelscope_vision_model_id,
            temperature=temperature if temperature is not None else 0.1
        )

    def _get_tools(self) -> list:
        return []

    def _get_system_prompt(self) -> str:
        return "你是一个视觉分析助手，能够分析图片内容并回答相关问题。请用中文回答。"

    def _build_multimodal_messages(self, task: str, images: List[str]) -> list:
        content = [{"type": "text", "text": task}]
        for image in images:
            content.append({"type": "image_url", "image_url": {"url": image}})
        return [HumanMessage(content=content)]

    async def execute(self, task: str, context: Optional[Dict[str, Any]] = None,
                      images: Optional[List[str]] = None) -> Dict[str, Any]:
        try:
            if not images or not isinstance(images, list) or len(images) == 0:
                return {
                    "success": False,
                    "message": "No image provided",
                    "data": {"input": task, "output": ""},
                    "error": "Image data is required for vision analysis"
                }

            logger.info(f"VisionAgent processing task: {task[:50]}...")
            messages = self._build_multimodal_messages(task, images)
            response = await self.llm.ainvoke(messages)

            output = response.content if hasattr(response, 'content') else str(response)
            if not output:
                return {
                    "success": False,
                    "message": "Empty response",
                    "data": {"input": task, "output": ""},
                    "error": "Model returned empty content"
                }

            logger.info("VisionAgent completed successfully")
            return {
                "success": True,
                "message": "Image analysis completed",
                "data": {"input": task, "output": output},
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

    async def stream_execute(self, task: str, context: Optional[Dict[str, Any]] = None,
                             images: Optional[List[str]] = None) -> AsyncGenerator[str, None]:
        try:
            if not images or not isinstance(images, list) or len(images) == 0:
                yield "错误：未提供图片数据"
                return

            logger.info(f"VisionAgent streaming task: {task[:50]}...")
            messages = self._build_multimodal_messages(task, images)

            async for chunk in self.llm.astream(messages):
                if chunk.content:
                    yield chunk.content

            logger.info("VisionAgent streaming completed")
        except Exception as e:
            error_msg = str(e)
            logger.exception(f"VisionAgent streaming failed: {error_msg}")
            if "not support" in error_msg.lower() or "vision" in error_msg.lower():
                error_msg = "当前模型不支持图像分析功能，请使用支持视觉的模型"
            yield f"处理失败: {error_msg}"