import json
import sys
import io
import contextlib
import logging
from typing import Dict, List, Any, Tuple
from langchain_core.tools import tool
from utils.tools.code_reviewer import code_quality_check, security_review, best_practices_advisor

logging.basicConfig(level=logging.INFO)

class PythonTestRunner:
    """Python代码测试运行器"""
    
    def __init__(self):
        self.timeout = 5  # 代码执行超时时间（秒）
    
    def run_code_with_tests(self, code: str, test_cases: List[Dict]) -> Dict[str, Any]:
        """
        运行用户代码并进行测试
        
        Args:
            code: 用户提交的代码
            test_cases: 测试用例列表，每个测试用例包含input和expected_output
            
        Returns:
            测试结果字典
        """
        result = {
            "execution_success": False,
            "execution_output": "",
            "execution_error": "",
            "test_results": [],
            "total_tests": len(test_cases),
            "passed_tests": 0,
            "score": 0.0
        }
        
        try:
            # 首先检查代码是否可以正常执行
            execution_result = self._execute_code(code)
            if execution_result["error"]:
                result["execution_error"] = execution_result["error"]
                return result
            
            result["execution_success"] = True
            result["execution_output"] = execution_result["output"]
            
            # 运行测试用例
            for i, test_case in enumerate(test_cases):
                test_result = self._run_single_test(code, test_case, i + 1)
                result["test_results"].append(test_result)
                if test_result["passed"]:
                    result["passed_tests"] += 1
            
            # 计算得分
            result["score"] = (result["passed_tests"] / result["total_tests"]) * 100 if result["total_tests"] > 0 else 0
            
        except Exception as e:
            logging.error(f"测试运行出错: {str(e)}")
            result["execution_error"] = f"测试运行出错: {str(e)}"
            
        return result
    
    def _execute_code(self, code: str) -> Dict[str, str]:
        """执行代码并捕获输出"""
        output = io.StringIO()
        error_output = io.StringIO()
        
        try:
            # 准备执行环境
            global_env = {
                '__builtins__': __builtins__,
                'print': lambda *args, **kwargs: print(*args, file=output, **kwargs),
                'input': lambda x='': '',  # 禁用input，避免阻塞
                'open': lambda *args, **kwargs: None,  # 禁用文件操作
            }
            
            with contextlib.redirect_stderr(error_output):
                # 尝试执行代码
                exec(code, global_env)
                
                # 如果代码中有表达式结果，尝试获取最后一个表达式的值
                lines = code.strip().split('\n')
                if lines:
                    last_line = lines[-1].strip()
                    # 如果最后一行不是语句（没有赋值、没有函数调用等），尝试eval
                    if (last_line and 
                        not last_line.startswith(('def ', 'class ', 'if ', 'for ', 'while ', 'try ', 'with ')) and
                        '=' not in last_line and 
                        not last_line.endswith(':') and
                        not last_line.startswith('print(')):
                        try:
                            result = eval(last_line, global_env)
                            if result is not None:
                                print(result, file=output)
                        except:
                            # 如果eval失败，忽略
                            pass
                            
            output_text = output.getvalue()
            error_text = error_output.getvalue()
            
            # 如果没有任何输出且没有错误，返回提示
            if not output_text and not error_text:
                output_text = "代码执行完成（无输出）"
                
            return {
                "output": output_text,
                "error": error_text
            }
        except Exception as e:
            return {
                "output": output.getvalue(),
                "error": str(e)
            }
    
    def _run_single_test(self, code: str, test_case: Dict, test_num: int) -> Dict[str, Any]:
        """运行单个测试用例"""
        test_result = {
            "test_number": test_num,
            "input": test_case.get("input", ""),
            "expected_output": test_case.get("expected_output", ""),
            "actual_output": "",
            "passed": False,
            "error": ""
        }
        
        try:
            # 模拟输入输出
            input_lines = test_case.get("input", "").split('\n')
            input_iter = iter(input_lines)
            
            output = io.StringIO()
            error_output = io.StringIO()
            
            # 准备测试环境
            global_env = {
                '__builtins__': __builtins__,
                'print': lambda *args, **kwargs: print(*args, file=output, **kwargs),
                'input': lambda prompt='': next(input_iter, ''),
                '__name__': '__main__'  # 确保测试代码能执行
            }
            
            try:
                with contextlib.redirect_stderr(error_output):
                    # 执行代码
                    exec(code, global_env)
                    
                actual_output = output.getvalue().strip()
                expected_output = str(test_case.get("expected_output", "")).strip()
                
                test_result["actual_output"] = actual_output
                
                # 比较输出结果
                if actual_output == expected_output:
                    test_result["passed"] = True
                else:
                    test_result["passed"] = False
                
                # 检查是否有错误
                error_text = error_output.getvalue()
                if error_text:
                    test_result["error"] = error_text
                    test_result["passed"] = False
                    
            except Exception as e:
                test_result["error"] = str(e)
                test_result["passed"] = False
                test_result["actual_output"] = f"执行错误: {str(e)}"
                
        except Exception as e:
            test_result["error"] = f"测试环境错误: {str(e)}"
            test_result["actual_output"] = ""
            
        return test_result

@tool
def execute_python_code(code: str) -> Dict[str, Any]:
    """
    执行Python代码并返回结果
    
    Args:
        code: 要执行的Python代码
        
    Returns:
        执行结果字典
    """
    logging.info("Tool: execute_python_code")
    runner = PythonTestRunner()
    return runner._execute_code(code)

@tool  
def run_python_tests(code: str, test_cases_json: str) -> Dict[str, Any]:
    """
    运行Python代码测试
    
    Args:
        code: 用户代码
        test_cases_json: 测试用例JSON字符串
        
    Returns:
        测试结果字典
    """
    logging.info("Tool: run_python_tests")
    try:
        test_cases = json.loads(test_cases_json)
        runner = PythonTestRunner()
        return runner.run_code_with_tests(code, test_cases)
    except json.JSONDecodeError as e:
        return {"error": f"测试用例格式错误: {str(e)}"}