from peewee import CharField, TextField, IntegerField, DateTimeField, ForeignKeyField, BooleanField, FloatField
from datetime import datetime
from pydantic import BaseModel as PydanticBaseModel
from typing import Optional, Dict, Any, List
from database.models.base import BaseModel
from database.models.user import User

class PythonQuestion(BaseModel):
    """Python题目模型"""
    title = CharField(max_length=255)  # 题目标题
    description = TextField()  # 题目描述
    difficulty = IntegerField()  # 难度等级 1-5
    example_input = TextField(null=True)  # 示例输入
    example_output = TextField(null=True)  # 示例输出
    test_cases = TextField()  # 测试用例（JSON格式）
    template_code = TextField(null=True)  # 模板代码
    created_at = DateTimeField(default=datetime.now)
    is_active = BooleanField(default=True)

    class Meta:
        table_name = 'python_questions'

class PythonTestSession(BaseModel):
    """Python测试会话模型"""
    user_id = ForeignKeyField(User, backref='python_test_sessions')
    session_name = CharField(max_length=255, default='Python测试')
    questions = TextField()  # 本次测试的题目ID列表（JSON格式）
    current_question_index = IntegerField(default=0)  # 当前题目索引
    total_score = FloatField(default=0.0)  # 总分
    status = CharField(max_length=20, default='in_progress')  # 状态：in_progress, completed
    started_at = DateTimeField(default=datetime.now)
    completed_at = DateTimeField(null=True)
    report = TextField(null=True)  # 测试报告（JSON格式）

    class Meta:
        table_name = 'python_test_sessions'

class PythonSubmission(BaseModel):
    """Python代码提交记录"""
    session_id = ForeignKeyField(PythonTestSession, backref='submissions')
    question_id = ForeignKeyField(PythonQuestion, backref='submissions')
    user_code = TextField()  # 用户提交的代码
    execution_result = TextField(null=True)  # 执行结果
    test_results = TextField(null=True)  # 测试结果（JSON格式）
    review_result = TextField(null=True)  # 代码审查结果（JSON格式）
    score = FloatField(default=0.0)  # 得分
    is_passed = BooleanField(default=False)  # 是否通过
    submitted_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = 'python_submissions'

# Pydantic模型用于API
class PythonQuestionCreate(PydanticBaseModel):
    title: str
    description: str
    difficulty: int
    example_input: Optional[str] = None
    example_output: Optional[str] = None
    test_cases: str  # JSON字符串
    template_code: Optional[str] = None

class PythonQuestionResponse(PydanticBaseModel):
    id: int
    title: str
    description: str
    difficulty: int
    example_input: Optional[str] = None
    example_output: Optional[str] = None
    template_code: Optional[str] = None
    created_at: str

class PythonTestSessionCreate(PydanticBaseModel):
    session_name: Optional[str] = 'Python测试'

class PythonTestSessionResponse(PydanticBaseModel):
    id: int
    session_name: str
    questions: List[int]  # 题目ID列表
    current_question_index: int
    total_score: float
    status: str
    started_at: str
    completed_at: Optional[str] = None
    report: Optional[Dict[str, Any]] = None

class PythonSubmissionCreate(PydanticBaseModel):
    session_id: int
    question_id: int
    user_code: str

class PythonSubmissionResponse(PydanticBaseModel):
    id: int
    session_id: int
    question_id: int
    user_code: str
    execution_result: Optional[str] = None
    test_results: Optional[Dict[str, Any]] = None
    review_result: Optional[Dict[str, Any]] = None
    score: float
    is_passed: bool
    submitted_at: str

class TestReportResponse(PydanticBaseModel):
    session_id: int
    total_score: float
    questions_attempted: int
    questions_passed: int
    difficulty_analysis: Dict[str, Any]
    skill_assessment: Dict[str, Any]
    recommendations: List[str]
    detailed_results: List[Dict[str, Any]]