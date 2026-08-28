from langchain.tools import BaseTool
from typing import Type, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import httpx
from app.config import settings
from loguru import logger


class TrendingSearchInput(BaseModel):
    language: str = Field(default="", description="编程语言过滤，如 python、javascript、go，留空表示不限")
    since: str = Field(default="weekly", description="时间范围: daily / weekly / monthly")
    limit: int = Field(default=10, ge=1, le=30, description="返回条数，默认10")


class TrendingSearchTool(BaseTool):
    name: str = "trending_search"
    description: str = "搜索 GitHub 热门开源项目，可按语言和时间范围过滤"
    args_schema: Type[BaseModel] = TrendingSearchInput

    def _build_query(self, language: str, since: str) -> str:
        """构建 GitHub Search API 查询条件"""
        now = datetime.utcnow()
        delta = {"daily": timedelta(days=1), "weekly": timedelta(days=7), "monthly": timedelta(days=30)}.get(since, timedelta(days=7))
        date_str = (now - delta).strftime("%Y-%m-%d")

        parts = [f"created:>{date_str}"]
        if language:
            parts.append(f"language:{language}")
        return " ".join(parts)

    async def _arun(self, language: str = "", since: str = "weekly", limit: int = 10) -> str:
        query = self._build_query(language, since)
        headers = {"Accept": "application/vnd.github+json"}
        if settings.github_token:
            headers["Authorization"] = f"Bearer {settings.github_token}"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    "https://api.github.com/search/repositories",
                    params={"q": query, "sort": "stars", "order": "desc", "per_page": limit},
                    headers=headers,
                    timeout=15.0
                )
                response.raise_for_status()
                data = response.json()

                if not data.get("items"):
                    return f"未找到{'语言为 ' + language + ' 的' if language else ''}近期热门项目"

                lines = [f"=== {'语言: ' + language + ' | ' if language else ''}{since} 热门开源项目 (Top {len(data['items'])}) ==="]
                for i, repo in enumerate(data["items"], 1):
                    desc = (repo.get("description") or "无描述")[:60]
                    lines.append(
                        f"{i}. **{repo['full_name']}**  ⭐{repo['stargazers_count']}  "
                        f"语言: {repo.get('language') or 'N/A'}\n"
                        f"   {desc}\n"
                        f"   {repo['html_url']}"
                    )
                return "\n\n".join(lines)

            except httpx.HTTPStatusError as e:
                logger.error(f"GitHub API error: {e.response.status_code} - {e.response.text}")
                return f"GitHub API 请求失败 (HTTP {e.response.status_code})"
            except Exception as e:
                logger.exception(f"Trending search failed: {e}")
                return f"搜索失败: {str(e)}"

    def _run(self, language: str = "", since: str = "weekly", limit: int = 10) -> str:
        import asyncio
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self._arun(language, since, limit))
        raise RuntimeError("_run() cannot be called from async context, use _arun() instead")