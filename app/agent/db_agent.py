from typing import List
from app.agent.base import BaseAgent
from app.tools.db_tools import DatabaseQueryTool

class DatabaseAgent(BaseAgent):
    def _get_tools(self) -> List:
        return [DatabaseQueryTool()]
    
    def _get_system_prompt(self) -> str:
        return """你是一个专业的数据库代理，必须使用 database_query 工具来执行 SQL 查询。
        当用户要求查询数据库时：
        1. 你必须使用 database_query 工具执行 SQL 查询
        2. 首先检查表是否存在：SELECT * FROM information_schema.tables WHERE table_name = 'user'
        3. 然后执行实际查询：SELECT * FROM user
        4. 必须返回实际的查询结果，不能只描述步骤
        
        重要：在返回最终答案时，必须以 "Final Answer:" 开头，然后直接输出查询结果。
        例如：Final Answer: 查询结果：id=1, 姓名=张三, 邮箱=zhangsan@example.com, 年龄=25
        
        你必须使用工具来执行查询，不要只描述步骤。"""
