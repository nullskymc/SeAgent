import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage

from adapter.openai_api import model
from utils.tools.python_tester import execute_python_code, run_python_tests
from utils.tools.code_reviewer import code_quality_check, security_review, best_practices_advisor

logging.basicConfig(level=logging.INFO)

# Python代码审查专家提示
PYTHON_EXPERT_PROMPT = """你是一名资深的Python开发专家，专门负责代码审查和技能评估。你的任务是：

1. **代码质量分析**：分析代码的结构、命名规范、可读性等
2. **技能水平评估**：基于代码复杂度、使用的技术、解决方案质量评估开发者水平
3. **改进建议**：提供具体的代码改进建议和学习方向
4. **最佳实践指导**：推荐Python开发的最佳实践

请用中文回答，语调友好专业。你会收到以下信息：
- 题目要求和难度等级
- 用户提交的代码
- 测试运行结果
- 代码质量检查结果（如果可用）

请综合这些信息，给出详细的分析和建议。

重要：你的评估应该包括：
1. 代码质量评分（1-10分）
2. 技能等级判断（入门/初级/中级/高级）
3. 优点和不足
4. 具体的改进建议
5. 推荐的学习资源或方向
"""

class PythonCodeReviewAgent:
    """Python代码审查智能体"""
    
    def __init__(self):
        # 创建工具列表
        self.tools = [
            execute_python_code,
            run_python_tests,
            code_quality_check,
            security_review,
            best_practices_advisor
        ]
        
        # 创建提示模板
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", PYTHON_EXPERT_PROMPT),
            ("human", "{question}"),
            MessagesPlaceholder(variable_name='agent_scratchpad'),
        ])
        
        # 创建代理
        self.agent = create_tool_calling_agent(model, self.tools, self.prompt)
        self.executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=False,
            handle_parsing_errors=True,
            max_iterations=3
        )
    
    async def review_code_submission(self, 
                                   question_title: str,
                                   question_description: str, 
                                   question_difficulty: int,
                                   user_code: str, 
                                   test_results: Dict) -> Dict[str, Any]:
        """
        审查单个代码提交
        """
        # 简化的审查请求，避免复杂的工具调用
        review_request = f"""
请审查以下Python代码：

题目：{question_title}
难度：{question_difficulty}/5
代码：
```python
{user_code}
```

测试通过：{test_results.get('passed_tests', 0)}/{test_results.get('total_tests', 0)}

请直接给出评估：
1. 代码质量分数(1-10)
2. 技能等级(入门/初级/中级/高级)
3. 优点
4. 改进建议
"""
        
        try:
            # 直接调用模型，不使用复杂的agent executor
            from adapter.openai_api import model
            
            messages = [
                {"role": "system", "content": PYTHON_EXPERT_PROMPT},
                {"role": "user", "content": review_request}
            ]
            
            # 使用模型直接生成回复
            response = model.invoke(messages)
            agent_output = response.content if hasattr(response, 'content') else str(response)
            
            # 解析结果
            return self._parse_review_result(agent_output, test_results)
            
        except Exception as e:
            logging.error(f"代码审查出错: {e}")
            # 返回基础分析作为备用
            return self._basic_analysis(user_code, test_results, question_difficulty)
    
    async def generate_session_report(self, session_data: List[Dict]) -> Dict[str, Any]:
        """
        生成整个测试会话的综合报告
        
        Args:
            session_data: 会话数据，包含所有题目的提交信息
            
        Returns:
            综合报告
        """
        # 构建会话报告请求
        session_summary = []
        for i, submission in enumerate(session_data, 1):
            session_summary.append(f"""
题目 {i}: {submission.get('question_title', f'题目{i}')}
- 难度: {submission.get('difficulty', 'unknown')}/5
- 测试通过: {submission.get('test_passed', 0)}/{submission.get('test_total', 0)}
- 代码长度: {len(submission.get('user_code', '').split('\n'))} 行
""")
        
        report_request = f"""
请基于以下Python测试会话数据生成综合技能评估报告：

**会话概览：**
- 总题目数：{len(session_data)}
- 题目分布：{', '.join([f"难度{submission.get('difficulty', 'unknown')}" for submission in session_data])}

**各题目概况：**
{''.join(session_summary)}

**详细代码分析：**
请分析每道题目的代码质量和实现方式，然后给出：

1. 总体技能水平评估（入门/初级/中级/高级）
2. 各难度等级的表现分析
3. 编程能力强项和弱项
4. 学习建议和改进方向
5. 推荐的进阶学习路径

请用JSON格式返回结果，包含：
- overall_skill_level: 总体技能等级
- skill_score: 综合技能分数(0-100)
- difficulty_performance: 各难度表现分析
- strengths: 编程强项
- improvement_areas: 需改进领域  
- learning_path: 推荐学习路径
- detailed_feedback: 详细反馈
"""
        
        try:
            # 直接使用模型生成，避免复杂的智能体调用
            messages = [
                {"role": "system", "content": PYTHON_EXPERT_PROMPT},
                {"role": "user", "content": report_request}
            ]
            
            response = model.invoke(messages)
            agent_output = response.content if hasattr(response, 'content') else str(response)
            
            # 解析结果
            return self._parse_session_report(agent_output, session_data)
            
        except Exception as e:
            logging.error(f"生成会话报告出错: {e}")
            # 返回基础报告作为备用
            return self._basic_session_report(session_data)
    
    def _parse_review_result(self, agent_output: str, test_results: Dict) -> Dict[str, Any]:
        """解析智能体输出的审查结果"""
        try:
            # 尝试从输出中提取JSON
            import re
            json_match = re.search(r'\{.*\}', agent_output, re.DOTALL)
            if json_match:
                parsed_result = json.loads(json_match.group())
                return {
                    "quality_score": parsed_result.get("quality_score", 5),
                    "skill_level": parsed_result.get("skill_level", "初级"),
                    "strengths": parsed_result.get("strengths", []),
                    "weaknesses": parsed_result.get("weaknesses", []),
                    "suggestions": parsed_result.get("suggestions", []),
                    "learning_recommendations": parsed_result.get("learning_recommendations", []),
                    "detailed_analysis": parsed_result.get("detailed_analysis", agent_output)
                }
            else:
                # 如果没有JSON格式，使用原始输出
                return {
                    "quality_score": 6,
                    "skill_level": "中级",
                    "strengths": ["完成了题目要求"],
                    "weaknesses": [],
                    "suggestions": [],
                    "learning_recommendations": [],
                    "detailed_analysis": agent_output
                }
        except:
            # 解析失败，返回基础结果
            return self._basic_analysis("", test_results, 2)
    
    def _parse_session_report(self, agent_output: str, session_data: List[Dict]) -> Dict[str, Any]:
        """解析会话报告结果"""
        try:
            import re
            json_match = re.search(r'\{.*\}', agent_output, re.DOTALL)
            if json_match:
                parsed_result = json.loads(json_match.group())
                return parsed_result
            else:
                return {
                    "overall_skill_level": "中级",
                    "skill_score": 60,
                    "difficulty_performance": {},
                    "strengths": [],
                    "improvement_areas": [],
                    "learning_path": [],
                    "detailed_feedback": agent_output
                }
        except:
            return self._basic_session_report(session_data)
    
    def _basic_analysis(self, code: str, test_results: Dict, difficulty: int) -> Dict[str, Any]:
        """基础分析作为备用"""
        test_score = test_results.get('score', 0)
        
        # 简单的技能等级判断
        if test_score >= 90:
            skill_level = "高级"
            quality_score = 8
        elif test_score >= 70:
            skill_level = "中级" 
            quality_score = 6
        elif test_score >= 50:
            skill_level = "初级"
            quality_score = 5
        else:
            skill_level = "入门"
            quality_score = 3
            
        return {
            "quality_score": quality_score,
            "skill_level": skill_level,
            "strengths": ["能够运行代码"] if test_results.get('execution_success') else [],
            "weaknesses": ["测试通过率有待提高"] if test_score < 80 else [],
            "suggestions": ["多练习编程题目，提高代码质量"],
            "learning_recommendations": ["Python基础语法", "算法和数据结构"],
            "detailed_analysis": f"基于测试结果的基础分析，测试得分：{test_score}%"
        }
    
    def _basic_session_report(self, session_data: List[Dict]) -> Dict[str, Any]:
        """基础会话报告作为备用"""
        total_questions = len(session_data)
        passed_questions = sum(1 for s in session_data if s.get('passed', False))
        avg_score = sum(s.get('score', 0) for s in session_data) / total_questions if total_questions > 0 else 0
        
        if avg_score >= 80:
            skill_level = "高级"
        elif avg_score >= 60:
            skill_level = "中级"
        elif avg_score >= 40:
            skill_level = "初级"
        else:
            skill_level = "入门"
        
        # 生成难度分析
        difficulty_stats = {}
        for submission in session_data:
            difficulty = submission.get('difficulty', 1)
            if difficulty not in difficulty_stats:
                difficulty_stats[difficulty] = {
                    "attempted": 0,
                    "passed": 0,
                    "scores": [],
                    "average_score": 0,
                    "pass_rate": 0,
                    "difficulty_name": f"难度 {difficulty}"
                }
            
            difficulty_stats[difficulty]["attempted"] += 1
            if submission.get('passed', False):
                difficulty_stats[difficulty]["passed"] += 1
            difficulty_stats[difficulty]["scores"].append(submission.get('score', 0))
        
        # 计算统计数据
        for difficulty, stats in difficulty_stats.items():
            stats["average_score"] = sum(stats["scores"]) / len(stats["scores"]) if stats["scores"] else 0
            stats["pass_rate"] = stats["passed"] / stats["attempted"] if stats["attempted"] > 0 else 0
        
        # 找出最强和最弱领域
        strongest_area = None
        weakest_area = None
        if difficulty_stats:
            strongest_area = max(difficulty_stats.keys(), 
                               key=lambda x: difficulty_stats[x]["pass_rate"]) if difficulty_stats else None
            weakest_area = min(difficulty_stats.keys(), 
                              key=lambda x: difficulty_stats[x]["pass_rate"]) if len(difficulty_stats) > 1 else None
            
        return {
            "overall_skill_level": skill_level,
            "skill_score": avg_score,
            "difficulty_performance": {
                "difficulty_stats": difficulty_stats,
                "strongest_area": strongest_area,
                "weakest_area": weakest_area
            },
            "strengths": ["具备Python基础知识"],
            "improvement_areas": ["提高代码质量", "增强算法思维"],
            "learning_path": ["继续练习编程题目", "学习Python最佳实践"],
            "detailed_feedback": f"完成了{passed_questions}/{total_questions}道题目，平均得分{avg_score:.1f}分"
        }

# 全局实例
python_review_agent = PythonCodeReviewAgent()

async def review_python_code(question_title: str, question_description: str, question_difficulty: int, 
                           user_code: str, test_results: Dict) -> Dict[str, Any]:
    """
    使用智能体审查Python代码
    """
    return await python_review_agent.review_code_submission(
        question_title, question_description, question_difficulty, user_code, test_results
    )

async def generate_python_session_report(session_data: List[Dict]) -> Dict[str, Any]:
    """
    使用智能体生成Python测试会话报告  
    """
    return await python_review_agent.generate_session_report(session_data)