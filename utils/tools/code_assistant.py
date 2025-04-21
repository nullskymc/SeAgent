import logging
import re
import ast
import typing
from typing import Dict, List, Optional, Any
from langchain_core.tools import tool

logging.basicConfig(level=logging.INFO)

@tool
def code_analyzer(code: str) -> Dict:
    """
    分析提供的代码，返回代码结构信息，包括函数、类、导入等。
    
    Args:
        code: 要分析的代码字符串
        
    Returns:
        Dict: 代码分析结果，包括函数列表、类列表、导入列表等
    """
    logging.info("Tool: code_analyzer - 分析代码结构")
    result = {
        "functions": [],
        "classes": [],
        "imports": [],
        "variables": []
    }
    
    try:
        parsed_ast = ast.parse(code)
        
        # 分析导入
        for node in ast.walk(parsed_ast):
            if isinstance(node, ast.Import):
                for name in node.names:
                    result["imports"].append(name.name)
            elif isinstance(node, ast.ImportFrom):
                for name in node.names:
                    result["imports"].append(f"{node.module}.{name.name}")
            
            # 分析函数
            elif isinstance(node, ast.FunctionDef):
                func_info = {
                    "name": node.name,
                    "args": [arg.arg for arg in node.args.args],
                    "decorators": [ast.unparse(decorator) for decorator in node.decorator_list],
                    "lineno": node.lineno
                }
                result["functions"].append(func_info)
            
            # 分析类
            elif isinstance(node, ast.ClassDef):
                class_info = {
                    "name": node.name,
                    "bases": [ast.unparse(base) for base in node.bases],
                    "methods": [],
                    "lineno": node.lineno
                }
                
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        method_info = {
                            "name": item.name,
                            "args": [arg.arg for arg in item.args.args],
                            "decorators": [ast.unparse(decorator) for decorator in item.decorator_list]
                        }
                        class_info["methods"].append(method_info)
                        
                result["classes"].append(class_info)
                
            # 分析全局变量
            elif isinstance(node, ast.Assign) and all(isinstance(target, ast.Name) for target in node.targets):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        var_info = {
                            "name": target.id,
                            "value": ast.unparse(node.value),
                            "lineno": node.lineno
                        }
                        result["variables"].append(var_info)
    except Exception as e:
        return {"error": str(e)}
    
    return result

@tool
def code_generator(description: str, language: str = "python") -> str:
    """
    根据描述生成代码片段。
    
    Args:
        description: 代码功能描述
        language: 编程语言，默认为python
        
    Returns:
        str: 生成的代码字符串
    """
    logging.info(f"Tool: code_generator - 为{language}生成代码")
    
    # 这个工具主要作为一个提示，实际代码生成将由大语言模型完成
    # 这里返回提示信息，告诉代理通过自身能力生成代码
    return f"请根据以下描述生成{language}代码：{description}"

@tool
def code_fixer(code: str, error_message: str) -> str:
    """
    修复代码中的错误。
    
    Args:
        code: 有错误的代码
        error_message: 错误信息
        
    Returns:
        str: 修复建议或修复后的代码
    """
    logging.info("Tool: code_fixer - 尝试修复代码错误")
    
    # 这个工具作为提示，实际修复由大语言模型完成
    return f"请根据以下错误信息修复代码：{error_message}"

@tool
def code_documentation(code: str) -> str:
    """
    为代码生成文档字符串和注释。
    
    Args:
        code: 需要添加文档的代码
        
    Returns:
        str: 添加了文档字符串的代码
    """
    logging.info("Tool: code_documentation - 生成代码文档")
    
    try:
        # 解析代码
        parsed_ast = ast.parse(code)
        
        # 收集需要添加文档的函数和类
        functions = []
        classes = []
        
        for node in ast.walk(parsed_ast):
            if isinstance(node, ast.FunctionDef):
                functions.append({
                    "name": node.name,
                    "args": [arg.arg for arg in node.args.args],
                    "has_docstring": isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Str)
                })
            elif isinstance(node, ast.ClassDef):
                methods = []
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        methods.append({
                            "name": item.name,
                            "args": [arg.arg for arg in item.args.args],
                            "has_docstring": isinstance(item.body[0], ast.Expr) and isinstance(item.body[0].value, ast.Str)
                        })
                
                classes.append({
                    "name": node.name, 
                    "methods": methods,
                    "has_docstring": isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Str)
                })
        
        # 生成文档建议
        result = "已分析代码结构，以下是文档建议：\n\n"
        
        if not functions and not classes:
            result += "没有找到需要添加文档的函数或类。"
        
        for func in functions:
            if not func["has_docstring"]:
                args_str = ", ".join(func["args"])
                result += f"函数 {func['name']}({args_str}) 需要添加文档字符串\n"
        
        for cls in classes:
            if not cls["has_docstring"]:
                result += f"类 {cls['name']} 需要添加文档字符串\n"
            
            for method in cls["methods"]:
                if not method["has_docstring"]:
                    args_str = ", ".join(method["args"])
                    if "self" in args_str:
                        args_str = args_str.replace("self, ", "")
                        if args_str == "self":
                            args_str = ""
                    result += f"类 {cls['name']} 的方法 {method['name']}({args_str}) 需要添加文档字符串\n"
        
        return result
        
    except Exception as e:
        return f"分析代码时出错：{str(e)}"

@tool
def dependency_analyzer(code: str) -> Dict:
    """
    分析代码依赖，识别导入的库并提供安装建议。
    
    Args:
        code: 要分析的代码
        
    Returns:
        Dict: 依赖分析结果
    """
    logging.info("Tool: dependency_analyzer - 分析代码依赖")
    
    common_packages = {
        "numpy": "pip install numpy",
        "pandas": "pip install pandas",
        "matplotlib": "pip install matplotlib",
        "scikit-learn": "sklearn", "sklearn": "pip install scikit-learn",
        "tensorflow": "pip install tensorflow",
        "torch": "pip install torch",
        "flask": "pip install flask",
        "django": "pip install django",
        "requests": "pip install requests",
        "beautifulsoup4": "bs4", "bs4": "pip install beautifulsoup4",
        "pytest": "pip install pytest",
        "sqlalchemy": "pip install sqlalchemy",
        "langchain": "pip install langchain",
        "langchain_community": "pip install langchain-community",
        "langchain_core": "pip install langchain-core",
        "openai": "pip install openai"
    }
    
    result = {
        "imports": [],
        "install_commands": []
    }
    
    try:
        parsed_ast = ast.parse(code)
        
        # 收集所有导入
        for node in ast.walk(parsed_ast):
            if isinstance(node, ast.Import):
                for name in node.names:
                    base_package = name.name.split('.')[0]
                    result["imports"].append(base_package)
                    
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    base_package = node.module.split('.')[0]
                    result["imports"].append(base_package)
        
        # 移除重复项
        result["imports"] = list(set(result["imports"]))
        
        # 生成安装命令
        for package in result["imports"]:
            if package in common_packages:
                install_cmd = common_packages[package]
                if install_cmd not in result["install_commands"]:
                    result["install_commands"].append(install_cmd)
            else:
                install_cmd = f"pip install {package}"
                if install_cmd not in result["install_commands"]:
                    result["install_commands"].append(install_cmd)
    
    except Exception as e:
        return {"error": str(e)}
    
    return result