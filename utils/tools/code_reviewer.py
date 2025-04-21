import logging
import re
from typing import Dict, List, Optional
from langchain_core.tools import tool

logging.basicConfig(level=logging.INFO)

@tool
def code_quality_check(code: str, language: str = "python") -> Dict:
    """
    检查代码质量，并提供改进建议。
    
    Args:
        code: 要检查的代码
        language: 编程语言，默认为 python
        
    Returns:
        Dict: 包含代码质量评估结果和改进建议
    """
    logging.info(f"Tool: code_quality_check - 检查{language}代码质量")
    
    result = {
        "issues": [],
        "suggestions": [],
        "quality_score": 0
    }
    
    if language.lower() == "python":
        # 检查行长度
        lines = code.split('\n')
        for i, line in enumerate(lines):
            if len(line.strip()) > 100:
                result["issues"].append({
                    "line": i + 1,
                    "issue": "行长度超过100个字符",
                    "suggestion": "将长行拆分为多行，提高可读性"
                })
        
        # 检查命名规范
        variable_pattern = re.compile(r'\b[a-zA-Z_][a-zA-Z0-9_]*\s*=')
        function_pattern = re.compile(r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(')
        class_pattern = re.compile(r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)')
        
        for i, line in enumerate(lines):
            # 变量命名检查
            for var_match in variable_pattern.finditer(line):
                var_name = var_match.group(0).split('=')[0].strip()
                if var_name.isupper() and '_' not in var_name and len(var_name) > 1:
                    continue  # 全大写的常量命名是符合规范的
                if not var_name.islower() and '_' in var_name:
                    result["issues"].append({
                        "line": i + 1,
                        "issue": f"变量名 '{var_name}' 不符合 snake_case 命名规范",
                        "suggestion": f"使用小写字母和下划线，如 '{var_name.lower()}'"
                    })
            
            # 函数命名检查
            for func_match in function_pattern.finditer(line):
                func_name = func_match.group(1)
                if not func_name.islower() and '_' in func_name:
                    result["issues"].append({
                        "line": i + 1,
                        "issue": f"函数名 '{func_name}' 不符合 snake_case 命名规范",
                        "suggestion": f"使用小写字母和下划线，如 '{func_name.lower()}'"
                    })
            
            # 类命名检查
            for class_match in class_pattern.finditer(line):
                class_name = class_match.group(1)
                if not class_name[0].isupper() or '_' in class_name:
                    result["issues"].append({
                        "line": i + 1,
                        "issue": f"类名 '{class_name}' 不符合 PascalCase 命名规范",
                        "suggestion": f"使用大写字母开头且不含下划线，如 '{''.join(word.capitalize() for word in class_name.split('_'))}'"
                    })
        
        # 检查文档字符串
        docstring_pattern = re.compile(r'"""[\s\S]*?"""')
        if not docstring_pattern.search(code):
            result["suggestions"].append("代码缺少文档字符串，为函数和类添加描述性文档可提高代码可读性")
        
        # 计算质量得分
        if not result["issues"]:
            result["quality_score"] = 10
        else:
            issue_count = len(result["issues"])
            result["quality_score"] = max(1, 10 - issue_count)
    
    elif language.lower() in ["javascript", "typescript", "js", "ts"]:
        # 检查行长度
        lines = code.split('\n')
        for i, line in enumerate(lines):
            if len(line.strip()) > 100:
                result["issues"].append({
                    "line": i + 1,
                    "issue": "行长度超过100个字符",
                    "suggestion": "将长行拆分为多行，提高可读性"
                })
        
        # 检查命名规范
        variable_pattern = re.compile(r'\b(var|let|const)\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=')
        function_pattern = re.compile(r'function\s+([a-zA-Z_$][a-zA-Z0-9_$]*)')
        class_pattern = re.compile(r'class\s+([a-zA-Z_$][a-zA-Z0-9_$]*)')
        
        for i, line in enumerate(lines):
            # 变量命名检查
            for var_match in variable_pattern.finditer(line):
                var_name = var_match.group(2)
                if var_name[0] == '_':
                    result["issues"].append({
                        "line": i + 1,
                        "issue": f"变量名 '{var_name}' 以下划线开头，这在 JavaScript 中不是常见做法",
                        "suggestion": f"移除前导下划线，使用驼峰命名法 '{var_name.lstrip('_')}'"
                    })
                if var_name.isupper() and var_name != var_name.upper():
                    result["issues"].append({
                        "line": i + 1,
                        "issue": f"变量名 '{var_name}' 大小写混用但不是驼峰式",
                        "suggestion": "使用驼峰命名法 (camelCase)"
                    })
        
        # 检查注释
        if not re.search(r'^\s*\/\*\*[\s\S]*?\*\/', code, re.MULTILINE):
            result["suggestions"].append("代码缺少 JSDoc 风格注释，为函数和类添加 JSDoc 注释可提高代码可读性")
        
        # 计算质量得分
        if not result["issues"]:
            result["quality_score"] = 10
        else:
            issue_count = len(result["issues"])
            result["quality_score"] = max(1, 10 - issue_count)
    
    # 通用建议
    result["suggestions"].append("确保代码有适当的注释，特别是在复杂逻辑处")
    result["suggestions"].append("避免重复代码，考虑将重复逻辑提取为函数")
    result["suggestions"].append("使用有意义的变量和函数名，提高代码可读性")
    
    return result

@tool
def security_review(code: str, language: str = "python") -> Dict:
    """
    对代码进行安全性审查，检查常见的安全漏洞。
    
    Args:
        code: 要检查的代码
        language: 编程语言，默认为 python
        
    Returns:
        Dict: 包含安全漏洞和修复建议
    """
    logging.info(f"Tool: security_review - 审查{language}代码安全性")
    
    result = {
        "vulnerabilities": [],
        "risk_level": "low"
    }
    
    if language.lower() == "python":
        # 检查SQL注入
        sql_patterns = [
            (r'cursor\.execute\([^,)]*\%[^,)]*\)', "可能的SQL注入风险"),
            (r'cursor\.execute\([^,)]*\+[^,)]*\)', "可能的SQL注入风险"),
            (r'cursor\.execute\(f["\']', "可能的SQL注入风险 (f-string)"),
            (r'execute\(\s*["\'][^"\']*\{\s*[^}]*\}\s*["\']', "可能的SQL注入风险 (字符串格式化)")
        ]
        
        for pattern, message in sql_patterns:
            if re.search(pattern, code):
                result["vulnerabilities"].append({
                    "type": "SQL注入",
                    "description": message,
                    "suggestion": "使用参数化查询替代字符串拼接或格式化"
                })
        
        # 检查不安全的反序列化
        if re.search(r'pickle\.loads?\(|yaml\.load\((?!.*Loader=yaml\.SafeLoader)', code):
            result["vulnerabilities"].append({
                "type": "不安全的反序列化",
                "description": "使用了不安全的反序列化方法",
                "suggestion": "对于YAML，使用yaml.safe_load()；对于pickle，仅处理可信数据"
            })
        
        # 检查命令注入
        if re.search(r'os\.system\(|subprocess\.call\(|subprocess\.Popen\(|eval\(|exec\(', code):
            result["vulnerabilities"].append({
                "type": "命令注入",
                "description": "直接执行系统命令或动态代码",
                "suggestion": "避免直接执行用户输入；对必要的命令执行使用参数列表形式并严格验证输入"
            })
        
        # 检查敏感信息硬编码
        if re.search(r'password\s*=|api_key\s*=|secret\s*=|token\s*=', code, re.IGNORECASE):
            result["vulnerabilities"].append({
                "type": "硬编码敏感信息",
                "description": "代码中可能包含硬编码的密码或API密钥",
                "suggestion": "使用环境变量或配置文件存储敏感信息"
            })
        
        # 检查不安全的随机数生成
        if re.search(r'random\.(random|randint|choice)', code) and not re.search(r'secrets\.|cryptography', code):
            result["vulnerabilities"].append({
                "type": "不安全的随机数",
                "description": "使用了不加密的随机数生成方法",
                "suggestion": "对于安全敏感操作，使用secrets模块而非random模块"
            })
            
    elif language.lower() in ["javascript", "typescript", "js", "ts"]:
        # 检查XSS漏洞
        if re.search(r'innerHTML|outerHTML|document\.write\(', code):
            result["vulnerabilities"].append({
                "type": "XSS漏洞",
                "description": "直接操作DOM可能导致XSS攻击",
                "suggestion": "使用textContent替代innerHTML或使用安全的DOM操作库"
            })
        
        # 检查不安全的eval
        if re.search(r'eval\(|new Function\(', code):
            result["vulnerabilities"].append({
                "type": "不安全的动态代码执行",
                "description": "使用eval()或Function构造函数执行动态代码",
                "suggestion": "避免使用eval，寻找更安全的替代方案"
            })
        
        # 检查不安全的HTTP
        if re.search(r'http://', code) and not re.search(r'localhost|127\.0\.0\.1', code):
            result["vulnerabilities"].append({
                "type": "不安全的HTTP",
                "description": "使用了非加密的HTTP协议",
                "suggestion": "使用HTTPS替代HTTP"
            })
        
        # 检查硬编码敏感信息
        if re.search(r'password\s*=|apiKey\s*=|secret\s*=|token\s*=', code, re.IGNORECASE):
            result["vulnerabilities"].append({
                "type": "硬编码敏感信息",
                "description": "代码中可能包含硬编码的密码或API密钥",
                "suggestion": "使用环境变量或配置文件存储敏感信息"
            })
    
    # 确定风险等级
    vuln_count = len(result["vulnerabilities"])
    if vuln_count == 0:
        result["risk_level"] = "low"
    elif vuln_count <= 2:
        result["risk_level"] = "medium"
    else:
        result["risk_level"] = "high"
    
    return result

@tool
def best_practices_advisor(code: str, language: str = "python") -> List[Dict]:
    """
    根据编程语言的最佳实践，提供代码改进建议。
    
    Args:
        code: 要分析的代码
        language: 编程语言，默认为 python
        
    Returns:
        List[Dict]: 最佳实践建议列表
    """
    logging.info(f"Tool: best_practices_advisor - 提供{language}最佳实践建议")
    
    suggestions = []
    
    if language.lower() == "python":
        # 检查不必要的if-else
        if_else_count = len(re.findall(r'\bif\s+.*:\s*\n.*\belse\s*:', code))
        if if_else_count > 0:
            has_ternary = len(re.findall(r'\w+\s+if\s+.*\s+else\s+', code)) > 0
            if not has_ternary:
                suggestions.append({
                    "type": "简化条件语句",
                    "description": "代码中有多个if-else语句可能适合使用三元表达式简化",
                    "example": "result = value1 if condition else value2"
                })
        
        # 检查列表推导式用法
        for_in_list = len(re.findall(r'for\s+\w+\s+in\s+.*:.*\.append\(', code))
        if for_in_list > 0 and 'lambda' not in code:
            suggestions.append({
                "type": "使用列表推导式",
                "description": "使用for循环构建列表可以用列表推导式简化",
                "example": "new_list = [f(x) for x in old_list]"
            })
        
        # 检查with语句用法
        if 'open(' in code and 'with open' not in code:
            suggestions.append({
                "type": "使用上下文管理器",
                "description": "打开文件时应使用with语句确保资源正确关闭",
                "example": "with open('file.txt', 'r') as f:\n    content = f.read()"
            })
        
        # 检查字典获取值方式
        if re.search(r'if\s+\w+\s+in\s+\w+:\s*\n\s*.*=\s*\w+\[\w+\]', code):
            suggestions.append({
                "type": "使用字典get方法",
                "description": "使用字典的get方法可以简化键存在性检查",
                "example": "value = my_dict.get(key, default_value)"
            })
        
        # 检查f-string用法
        if '%' in code and 'f"' not in code and "f'" not in code:
            suggestions.append({
                "type": "使用f-string",
                "description": "使用f-string替代旧式的字符串格式化方法",
                "example": "message = f'Hello, {name}!'"
            })
            
    elif language.lower() in ["javascript", "typescript", "js", "ts"]:
        # 检查var的使用
        if re.search(r'\bvar\b', code):
            suggestions.append({
                "type": "使用let和const",
                "description": "避免使用var声明变量，优先使用const，其次使用let",
                "example": "const PI = 3.14; let counter = 0;"
            })
        
        # 检查箭头函数使用
        function_count = len(re.findall(r'function\s*\([^)]*\)', code))
        if function_count > 0 and '=>' not in code:
            suggestions.append({
                "type": "使用箭头函数",
                "description": "考虑使用箭头函数替代传统函数表达式",
                "example": "const add = (a, b) => a + b;"
            })
        
        # 检查解构赋值
        if re.search(r'\w+\[\d+\]|\w+\.\w+\s*=', code) and '{' in code and '}' in code:
            if not re.search(r'const\s*\{\s*\w+\s*\}', code):
                suggestions.append({
                    "type": "使用解构赋值",
                    "description": "使用解构赋值简化对象和数组的处理",
                    "example": "const { name, age } = person; const [first, ...rest] = items;"
                })
        
        # 检查模板字符串
        if '+' in code and '"' in code and "'" in code:
            if '`' not in code:
                suggestions.append({
                    "type": "使用模板字符串",
                    "description": "使用模板字符串替代字符串拼接",
                    "example": "const message = `Hello, ${name}!`;"
                })
        
        # 检查Promise使用
        if 'Promise' in code and 'async' not in code and 'await' not in code:
            suggestions.append({
                "type": "使用async/await",
                "description": "考虑使用async/await替代Promise链式调用",
                "example": "async function fetchData() {\n  const result = await fetch(url);\n  return await result.json();\n}"
            })
    
    return suggestions