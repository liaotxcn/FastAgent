from langchain.tools import BaseTool
from typing import Type
from pydantic.v1 import BaseModel, Field
import httpx
from app.config import settings
from loguru import logger

class MapSearchInput(BaseModel):
    location: str = Field(description="地点名称")

class MapSearchTool(BaseTool):
    name = "map_search"
    description = "搜索地点信息，参数为地点名称"
    args_schema: Type[BaseModel] = MapSearchInput
    
    async def _arun(self, location: str) -> str:
        """搜索地点信息"""
        try:
            url = f"{settings.amap_api_base}/v3/place/text"
            params = {
                "key": settings.amap_api_key,
                "keywords": location,
                "extensions": "base",
                "output": "json"
            }
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params)
                result = response.json()
                if result.get("status") == "1":
                    pois = result.get("pois", [])
                    if pois:
                        poi = pois[0]
                        return f"找到地点：{poi.get('name')}，地址：{poi.get('address')}，坐标：{poi.get('location')}"
                    return "未找到该地点"
                return f"搜索失败：{result.get('info', '未知错误')}"
        except Exception as e:
            logger.error(f"Map search failed: {e}")
            return f"搜索失败：{str(e)}"
    
    def _run(self, location: str) -> str:
        import asyncio
        return asyncio.run(self._arun(location))

class RoutePlanningInput(BaseModel):
    origin: str = Field(description="起点")
    destination: str = Field(description="终点")

class RoutePlanningTool(BaseTool):
    name = "route_planning"
    description = "规划路线，需要两个参数：origin（起点）和destination（终点），参数格式为JSON对象"
    args_schema: Type[BaseModel] = RoutePlanningInput
    
    async def _arun(self, origin: str, destination: str) -> str:
        """规划路线"""
        try:
            # 先获取起点和终点的坐标
            async def get_location(address):
                url = f"{settings.amap_api_base}/v3/geocode/geo"
                params = {
                    "key": settings.amap_api_key,
                    "address": address,
                    "output": "json"
                }
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, params=params)
                    result = response.json()
                    if result.get("status") == "1" and result.get("geocodes"):
                        return result["geocodes"][0]["location"]
                    return None
            
            origin_loc = await get_location(origin)
            dest_loc = await get_location(destination)
            
            if not origin_loc or not dest_loc:
                return "无法获取起点或终点的坐标"
            
            # 规划路线
            url = f"{settings.amap_api_base}/v3/direction/driving"
            params = {
                "key": settings.amap_api_key,
                "origin": origin_loc,
                "destination": dest_loc,
                "output": "json"
            }
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params)
                result = response.json()
                if result.get("status") == "1":
                    route = result.get("route", {})
                    paths = route.get("paths", [])
                    if paths:
                        path = paths[0]
                        distance = path.get("distance", "0")
                        duration = path.get("duration", "0")
                        steps = path.get("steps", [])
                        instructions = [step.get("instruction", "") for step in steps[:3]]
                        return f"路线规划成功：距离 {distance} 米，预计 {duration} 秒\n路线：{' → '.join(instructions)}"
                    return "路线规划失败"
                return f"路线规划失败：{result.get('info', '未知错误')}"
        except Exception as e:
            logger.error(f"Route planning failed: {e}")
            return f"路线规划失败：{str(e)}"
    
    def _run(self, origin: str, destination: str) -> str:
        import asyncio
        return asyncio.run(self._arun(origin, destination))