import json
import logging
from typing import List, Dict, Any
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool

from adapter.openai_api import model

logging.basicConfig(level=logging.INFO)

# Python题目生成专家提示
QUESTION_GENERATOR_PROMPT = """你是一名Python编程教育专家，专门负责生成编程练习题目。

你的任务是生成5道不同难度的Python编程题目，用于技能评估测试。

严格要求：
1. 只生成题目描述和空的函数模板，绝对不要提供任何答案实现
2. 函数体只能包含 pass 语句，不允许有任何实现代码
3. 不要在任何地方（包括注释、模板）暴露解题思路或答案
4. 难度递进：从基础语法到高级概念
5. 确保题目实用且有教育意义

请直接生成题目，不要使用工具。用中文描述题目。"""

@tool
def validate_python_code(code: str) -> Dict[str, Any]:
    """验证Python代码的语法正确性"""
    try:
        compile(code, '<string>', 'exec')
        return {"valid": True, "error": None}
    except SyntaxError as e:
        return {"valid": False, "error": str(e)}

class PythonQuestionGenerator:
    """Python题目生成智能体"""
    
    def __init__(self):
        # 创建工具列表
        self.tools = [validate_python_code]
        
        # 创建提示模板
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", QUESTION_GENERATOR_PROMPT),
            ("human", "{request}"),
        ])
    
    async def generate_questions(self) -> List[Dict[str, Any]]:
        """生成5道Python编程题目"""
        
        generation_request = """
请生成5道Python编程题目，按以下格式返回JSON：

```json
[
  {
    "title": "题目标题",
    "description": "详细的题目描述，说明要求实现什么功能",
    "difficulty": 1,
    "example_input": "示例输入",
    "example_output": "示例输出",
    "template_code": "包含空函数模板和基本测试的Python代码，函数体只有pass，不要提供实现"
  }
]
```

5道题目的难度要求：
- 第1题：难度1 - 基础语法（变量、运算符、简单函数）
- 第2题：难度2 - 字符串或列表操作
- 第3题：难度3 - 循环和条件判断的综合应用
- 第4题：难度4 - 算法思维（递归、排序等）
- 第5题：难度5 - 面向对象或复杂数据结构

重要要求：
1. template_code中的函数体必须只包含 pass 语句，绝对不要提供实现代码
2. 不要在任何地方暴露答案的实现思路或逻辑
3. 确保所有代码都是语法正确的Python代码  
4. 注重题目的教育价值和实用性
5. 测试用例仅用于说明期望的输入输出格式

示例template_code格式：
```python
def function_name(param):
    # 请在这里实现你的代码
    pass

# 测试你的代码
if __name__ == "__main__":
    # 示例用法
    result = function_name(example_input)
    print(result)
```
"""
        
        try:
            # 直接使用模型生成
            messages = [
                {"role": "system", "content": QUESTION_GENERATOR_PROMPT},
                {"role": "user", "content": generation_request}
            ]
            
            response = model.invoke(messages)
            agent_output = response.content if hasattr(response, 'content') else str(response)
            
            # 解析JSON结果
            questions = self._parse_questions(agent_output)
            
            # 验证生成的题目
            validated_questions = []
            for question in questions:
                if self._validate_question(question):
                    validated_questions.append(question)
                else:
                    logging.warning(f"题目验证失败: {question.get('title', 'Unknown')}")
            
            # 如果生成的有效题目不足5道，用备用题目补充
            if len(validated_questions) < 5:
                logging.warning(f"只生成了{len(validated_questions)}道有效题目，用备用题目补充")
                validated_questions.extend(self._get_fallback_questions()[len(validated_questions):])
            
            return validated_questions[:5]  # 确保只返回5道题
            
        except Exception as e:
            logging.error(f"题目生成出错: {e}")
            # 返回备用题目
            return self._get_fallback_questions()
    
    def _parse_questions(self, agent_output: str) -> List[Dict[str, Any]]:
        """解析智能体输出的题目"""
        try:
            import re
            
            # 清理输出，移除markdown格式
            cleaned_output = agent_output.strip()
            
            # 查找JSON代码块  
            json_patterns = [
                r'```json\s*(.*?)\s*```',  # ```json ... ```
                r'```\s*(.*?)\s*```',      # ``` ... ```
                r'\[\s*\{.*?\}\s*\]',      # [ { ... } ]
            ]
            
            json_str = None
            for pattern in json_patterns:
                match = re.search(pattern, cleaned_output, re.DOTALL)
                if match:
                    json_str = match.group(1) if '```' in pattern else match.group(0)
                    break
            
            if not json_str:
                logging.warning("未找到有效的JSON格式，使用备用题目")
                return []
            
            # 尝试修复常见的JSON格式问题
            json_str = json_str.strip()
            
            # 移除可能的代码注释
            json_str = re.sub(r'//.*?$', '', json_str, flags=re.MULTILINE)
            
            # 尝试解析JSON
            questions = json.loads(json_str)
            
            # 确保是列表格式
            if not isinstance(questions, list):
                questions = [questions]
            
            return questions
            
        except json.JSONDecodeError as e:
            logging.error(f"JSON解析失败: {e}")
            logging.debug(f"尝试解析的JSON: {json_str[:200] if json_str else 'None'}")
            return []
        except Exception as e:
            logging.error(f"解析题目出错: {e}")
            return []
    
    def _validate_question(self, question: Dict[str, Any]) -> bool:
        """验证题目的完整性和正确性"""
        required_fields = ['title', 'description', 'difficulty', 'template_code']
        
        # 检查必需字段
        for field in required_fields:
            if field not in question:
                logging.error(f"题目缺少必需字段: {field}")
                return False
        
        # 验证代码语法
        template_code = question.get('template_code', '')
        try:
            compile(template_code, '<string>', 'exec')
        except SyntaxError as e:
            logging.error(f"模板代码语法错误: {e}")
            return False
        
        # 检查是否包含答案实现（简单检测）
        if self._contains_implementation(template_code):
            logging.error(f"题目模板包含答案实现: {question.get('title')}")
            return False
        
        return True
    
    def _contains_implementation(self, code: str) -> bool:
        """检测代码是否包含实际实现（而不只是pass）"""
        # 移除注释和空行
        lines = []
        for line in code.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                lines.append(line)
        
        code_without_comments = '\n'.join(lines)
        
        # 查找函数定义
        import re
        function_blocks = re.findall(r'def\s+\w+\([^)]*\):[^def]*', code_without_comments, re.MULTILINE)
        
        for func_block in function_blocks:
            # 获取函数体部分
            lines = func_block.split('\n')[1:]  # 跳过函数定义行
            func_body_lines = []
            
            for line in lines:
                line = line.strip()
                if line:
                    # 跳过docstring
                    if line.startswith('"""') or line.startswith("'''"):
                        continue
                    func_body_lines.append(line)
            
            # 检查函数体是否只有pass
            non_pass_lines = [line for line in func_body_lines if line != 'pass']
            if non_pass_lines:
                # 如果有除了pass之外的语句，可能包含实现
                implementation_keywords = ['return', 'for', 'while', 'if', '=', 'append', 'extend']
                for line in non_pass_lines:
                    if any(keyword in line for keyword in implementation_keywords):
                        return True
        
        return False
    
    def _get_fallback_questions(self) -> List[Dict[str, Any]]:
        """获取备用题目（精简版）"""
        return [
            {
                "title": "数字相加",
                "description": "编写一个函数，接收两个整数并返回它们的和。",
                "difficulty": 1,
                "example_input": "3 5",
                "example_output": "8",
                "test_cases": [
                    {"input": "3 5", "expected_output": "8"},
                    {"input": "10 20", "expected_output": "30"},
                    {"input": "-5 3", "expected_output": "-2"},
                    {"input": "0 0", "expected_output": "0"}
                ],
                "template_code": """def add_numbers(a: int, b: int) -> int:
    # 请在这里实现你的代码
    pass

# 测试代码（请勿修改）
if __name__ == "__main__":
    nums = input().strip().split()
    a, b = int(nums[0]), int(nums[1])
    result = add_numbers(a, b)
    print(result)"""
            },
            {
                "title": "字符串反转",
                "description": "编写一个函数，接收一个字符串并返回其反转后的结果。",
                "difficulty": 2,
                "example_input": "hello",
                "example_output": "olleh",
                "test_cases": [
                    {"input": "hello", "expected_output": "olleh"},
                    {"input": "Python", "expected_output": "nohtyP"},
                    {"input": "123", "expected_output": "321"},
                    {"input": "a", "expected_output": "a"}
                ],
                "template_code": """def reverse_string(s: str) -> str:
    # 请在这里实现你的代码
    pass

# 测试代码（请勿修改）
if __name__ == "__main__":
    s = input().strip()
    result = reverse_string(s)
    print(result)"""
            },
            {
                "title": "查找最大值",
                "description": "编写一个函数，在一个数字列表中找出最大值，不使用内置的max函数。",
                "difficulty": 3,
                "example_input": "[1, 5, 3, 9, 2]",
                "example_output": "9",
                "test_cases": [
                    {"input": "[1, 5, 3, 9, 2]", "expected_output": "9"},
                    {"input": "[-1, -5, -3, -2]", "expected_output": "-1"},
                    {"input": "[100]", "expected_output": "100"},
                    {"input": "[7, 7, 7, 7]", "expected_output": "7"}
                ],
                "template_code": """def find_max(numbers: list) -> int:
    # 请在这里实现你的代码
    pass

# 测试代码（请勿修改）
if __name__ == "__main__":
    import ast
    numbers = ast.literal_eval(input().strip())
    result = find_max(numbers)
    print(result)"""
            },
            {
                "title": "斐波那契数列",
                "description": "实现斐波那契数列的第n项（n从0开始计算）。",
                "difficulty": 4,
                "example_input": "6",
                "example_output": "8",
                "test_cases": [
                    {"input": "0", "expected_output": "0"},
                    {"input": "1", "expected_output": "1"},
                    {"input": "6", "expected_output": "8"},
                    {"input": "10", "expected_output": "55"}
                ],
                "template_code": """def fibonacci(n: int) -> int:
    # 请在这里实现你的代码
    pass

# 测试代码（请勿修改）
if __name__ == "__main__":
    n = int(input().strip())
    result = fibonacci(n)
    print(result)"""
            },
            {
                "title": "简单计算器类",
                "description": "创建一个Calculator类，包含加、减、乘、除四个方法。",
                "difficulty": 5,
                "example_input": "add 10 5",
                "example_output": "15",
                "test_cases": [
                    {"input": "add 10 5", "expected_output": "15"},
                    {"input": "subtract 10 5", "expected_output": "5"},
                    {"input": "multiply 10 5", "expected_output": "50"},
                    {"input": "divide 10 5", "expected_output": "2"}
                ],
                "template_code": """class Calculator:
    def add(self, a: float, b: float) -> float:
        # 请在这里实现你的代码
        pass
    
    def subtract(self, a: float, b: float) -> float:
        # 请在这里实现你的代码
        pass
    
    def multiply(self, a: float, b: float) -> float:
        # 请在这里实现你的代码
        pass
    
    def divide(self, a: float, b: float) -> float:
        # 请在这里实现你的代码
        pass

# 测试代码（请勿修改）
if __name__ == "__main__":
    line = input().strip().split()
    operation, a, b = line[0], float(line[1]), float(line[2])
    calc = Calculator()
    
    if operation == "add":
        result = calc.add(a, b)
    elif operation == "subtract":
        result = calc.subtract(a, b)
    elif operation == "multiply":
        result = calc.multiply(a, b)
    elif operation == "divide":
        result = calc.divide(a, b)
    
    print(int(result) if result == int(result) else result)"""
            }
        ]

# 全局实例
question_generator = PythonQuestionGenerator()

async def generate_python_questions() -> List[Dict[str, Any]]:
    """
    使用智能体生成Python题目
    """
    return await question_generator.generate_questions()