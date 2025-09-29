import logging
import json
import random
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime

from database.models.python_test import (
    PythonQuestion, PythonTestSession, PythonSubmission,
    PythonQuestionCreate, PythonQuestionResponse,
    PythonTestSessionCreate, PythonTestSessionResponse,
    PythonSubmissionCreate, PythonSubmissionResponse,
    TestReportResponse
)
from database.models.user import User
from routes.auth import get_current_user
from utils.tools.python_tester import PythonTestRunner
from utils.python_review_agent import review_python_code, generate_python_session_report
from utils.python_question_generator import generate_python_questions

router = APIRouter()

# 注意：题目现在由智能体动态生成，不再使用硬编码数据

@router.post("/init-questions")
async def init_default_questions(current_user: User = Depends(get_current_user)):
    """使用智能体初始化默认题目"""
    try:
        # 检查是否已有题目
        existing_count = PythonQuestion.select().count()
        if existing_count >= 5:
            return {"message": f"题目已存在 {existing_count} 道，跳过初始化"}
        
        # 使用智能体生成题目
        logging.info("开始使用智能体生成Python题目...")
        questions = await generate_python_questions()
        
        # 保存题目到数据库
        created_count = 0
        for question_data in questions:
            try:
                PythonQuestion.create(
                    title=question_data.get("title", "未命名题目"),
                    description=question_data.get("description", ""),
                    difficulty=question_data.get("difficulty", 1),
                    example_input=question_data.get("example_input", ""),
                    example_output=question_data.get("example_output", ""),
                    test_cases=json.dumps([]),  # 空的测试用例
                    template_code=question_data.get("template_code", "")
                )
                created_count += 1
                logging.info(f"创建题目: {question_data.get('title')}")
                
            except Exception as e:
                logging.error(f"保存题目失败: {e}")
                continue
        
        return {"message": f"成功创建 {created_count} 道智能生成的题目"}
        
    except Exception as e:
        logging.exception(f"初始化题目失败: {e}")
        raise HTTPException(status_code=500, detail=f"初始化题目失败: {str(e)}")

@router.post("/regenerate-questions")
async def regenerate_questions(current_user: User = Depends(get_current_user)):
    """重新生成所有题目（替换现有题目）"""
    try:
        # 删除现有题目
        deleted_count = PythonQuestion.delete().execute()
        logging.info(f"删除了 {deleted_count} 道旧题目")
        
        # 使用智能体生成新题目
        logging.info("开始重新生成Python题目...")
        questions = await generate_python_questions()
        
        # 保存题目到数据库
        created_count = 0
        for question_data in questions:
            try:
                PythonQuestion.create(
                    title=question_data.get("title", "未命名题目"),
                    description=question_data.get("description", ""),
                    difficulty=question_data.get("difficulty", 1),
                    example_input=question_data.get("example_input", ""),
                    example_output=question_data.get("example_output", ""),
                    test_cases=json.dumps([]),  # 空的测试用例
                    template_code=question_data.get("template_code", "")
                )
                created_count += 1
                logging.info(f"创建新题目: {question_data.get('title')}")
                
            except Exception as e:
                logging.error(f"保存题目失败: {e}")
                continue
        
        return {
            "message": f"成功重新生成 {created_count} 道题目",
            "deleted": deleted_count,
            "created": created_count,
            "questions": [{"title": q.get("title"), "difficulty": q.get("difficulty")} for q in questions]
        }
        
    except Exception as e:
        logging.exception(f"重新生成题目失败: {e}")
        raise HTTPException(status_code=500, detail=f"重新生成题目失败: {str(e)}")

@router.get("/questions", response_model=List[PythonQuestionResponse])
async def get_questions(
    difficulty: Optional[int] = Query(None, description="难度等级筛选"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=50, description="每页数量"),
    current_user: User = Depends(get_current_user)
):
    """获取Python题目列表"""
    try:
        # 构建查询
        query = PythonQuestion.select().where(PythonQuestion.is_active == True)
        
        if difficulty is not None:
            query = query.where(PythonQuestion.difficulty == difficulty)
        
        # 分页
        total = query.count()
        questions = query.order_by(PythonQuestion.difficulty, PythonQuestion.id).paginate(page, size)
        
        result = []
        for question in questions:
            result.append(PythonQuestionResponse(
                id=question.id,
                title=question.title,
                description=question.description,
                difficulty=question.difficulty,
                example_input=question.example_input,
                example_output=question.example_output,
                template_code=question.template_code,
                created_at=question.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ))
        
        return result
    except Exception as e:
        logging.exception(f"获取题目列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取题目失败: {str(e)}")

@router.get("/questions/{question_id}", response_model=PythonQuestionResponse)
async def get_question(
    question_id: int,
    current_user: User = Depends(get_current_user)
):
    """获取单个题目详情"""
    try:
        question = PythonQuestion.get_or_none(
            (PythonQuestion.id == question_id) & (PythonQuestion.is_active == True)
        )
        
        if not question:
            raise HTTPException(status_code=404, detail="题目不存在")
        
        return PythonQuestionResponse(
            id=question.id,
            title=question.title,
            description=question.description,
            difficulty=question.difficulty,
            example_input=question.example_input,
            example_output=question.example_output,
            template_code=question.template_code,
            created_at=question.created_at.strftime('%Y-%m-%d %H:%M:%S')
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.exception(f"获取题目详情失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取题目失败: {str(e)}")

@router.post("/sessions", response_model=PythonTestSessionResponse)
async def create_test_session(
    session_data: PythonTestSessionCreate,
    current_user: User = Depends(get_current_user)
):
    """创建新的Python测试会话"""
    try:
        # 随机选择5道题目，难度分布：1道难度1，2道难度2，1道难度3，1道难度4
        difficulty_distribution = [1, 2, 2, 3, 4]
        selected_questions = []
        
        for difficulty in difficulty_distribution:
            questions = list(PythonQuestion.select().where(
                (PythonQuestion.difficulty == difficulty) & 
                (PythonQuestion.is_active == True)
            ))
            
            if questions:
                selected_question = random.choice(questions)
                selected_questions.append(selected_question.id)
        
        if len(selected_questions) < 5:
            # 如果某些难度的题目不够，随机补充
            all_questions = list(PythonQuestion.select().where(PythonQuestion.is_active == True))
            while len(selected_questions) < 5 and len(all_questions) > len(selected_questions):
                question = random.choice(all_questions)
                if question.id not in selected_questions:
                    selected_questions.append(question.id)
        
        # 创建测试会话
        session = PythonTestSession.create(
            user_id=current_user.id,
            session_name=session_data.session_name,
            questions=json.dumps(selected_questions),
            current_question_index=0,
            total_score=0.0,
            status='in_progress'
        )
        
        return PythonTestSessionResponse(
            id=session.id,
            session_name=session.session_name,
            questions=selected_questions,
            current_question_index=session.current_question_index,
            total_score=session.total_score,
            status=session.status,
            started_at=session.started_at.strftime('%Y-%m-%d %H:%M:%S')
        )
    except Exception as e:
        logging.exception(f"创建测试会话失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建测试会话失败: {str(e)}")

@router.get("/sessions/{session_id}", response_model=PythonTestSessionResponse)
async def get_test_session(
    session_id: int,
    current_user: User = Depends(get_current_user)
):
    """获取测试会话详情"""
    try:
        session = PythonTestSession.get_or_none(
            (PythonTestSession.id == session_id) & (PythonTestSession.user_id == current_user.id)
        )
        
        if not session:
            raise HTTPException(status_code=404, detail="测试会话不存在")
        
        questions = json.loads(session.questions) if session.questions else []
        report = json.loads(session.report) if session.report else None
        
        return PythonTestSessionResponse(
            id=session.id,
            session_name=session.session_name,
            questions=questions,
            current_question_index=session.current_question_index,
            total_score=session.total_score,
            status=session.status,
            started_at=session.started_at.strftime('%Y-%m-%d %H:%M:%S'),
            completed_at=session.completed_at.strftime('%Y-%m-%d %H:%M:%S') if session.completed_at else None,
            report=report
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.exception(f"获取测试会话失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取测试会话失败: {str(e)}")

@router.post("/submit", response_model=PythonSubmissionResponse)
async def submit_code(
    submission_data: PythonSubmissionCreate,
    current_user: User = Depends(get_current_user)
):
    """提交Python代码"""
    try:
        # 验证会话权限
        session = PythonTestSession.get_or_none(
            (PythonTestSession.id == submission_data.session_id) & 
            (PythonTestSession.user_id == current_user.id)
        )
        
        if not session:
            raise HTTPException(status_code=404, detail="测试会话不存在")
        
        if session.status == 'completed':
            raise HTTPException(status_code=400, detail="测试会话已完成")
        
        # 获取题目
        question = PythonQuestion.get_or_none(PythonQuestion.id == submission_data.question_id)
        if not question:
            raise HTTPException(status_code=404, detail="题目不存在")
        
        # 执行简单的代码运行检查（不执行复杂测试用例）
        runner = PythonTestRunner()
        basic_result = runner._execute_code(submission_data.user_code)
        
        # 使用智能体进行代码评估（主要评估方式）
        review_result = await review_python_code(
            question.title,
            question.description, 
            question.difficulty,
            submission_data.user_code,
            {"execution_success": not bool(basic_result.get("error", "")), "output": basic_result.get("output", "")}
        )
        
        # 根据智能体评估确定分数和通过状态
        quality_score = review_result.get("quality_score", 5)  # 1-10分
        final_score = (quality_score / 10) * 100  # 转换为百分制
        is_passed = quality_score >= 6  # 6分以上算通过
        
        # 创建提交记录
        submission = PythonSubmission.create(
            session_id=submission_data.session_id,
            question_id=submission_data.question_id,
            user_code=submission_data.user_code,
            execution_result=basic_result.get("output", "") or basic_result.get("error", "执行完成"),
            test_results=json.dumps({"ai_evaluation": True, "score": final_score}),
            review_result=json.dumps(review_result),
            score=final_score,
            is_passed=is_passed
        )
        
        # 更新会话进度
        questions_list = json.loads(session.questions)
        current_index = session.current_question_index
        
        if current_index < len(questions_list) - 1:
            # 更新到下一题
            PythonTestSession.update(
                current_question_index=current_index + 1,
                total_score=session.total_score + final_score
            ).where(PythonTestSession.id == session.id).execute()
        else:
            # 完成测试，使用智能体生成报告
            total_score = session.total_score + final_score
            
            # 准备智能体分析用的数据
            session_data_for_agent = []
            all_submissions = list(PythonSubmission.select().where(
                PythonSubmission.session_id == session.id
            )) + [submission]  # 包含当前提交
            
            for sub in all_submissions:
                sub_question = PythonQuestion.get_by_id(sub.question_id)
                review_data = json.loads(sub.review_result) if sub.review_result else {}
                
                session_data_for_agent.append({
                    "question_title": sub_question.title,
                    "difficulty": sub_question.difficulty,
                    "user_code": sub.user_code,
                    "score": sub.score,
                    "passed": sub.is_passed,
                    "review_result": review_data
                })
            
            # 生成最终报告
            try:
                report = await generate_python_session_report(session_data_for_agent)
            except Exception as ai_error:
                logging.error(f"生成会话报告出错: {ai_error}")
                # 使用简化的基础报告
                total_score_avg = total_score / len(all_submissions) if all_submissions else 0
                report = {
                    "overall_skill_level": "中级" if total_score_avg >= 60 else "初级",
                    "skill_score": total_score_avg,
                    "difficulty_performance": {},
                    "strengths": ["具备Python基础编程能力"],
                    "improvement_areas": ["提高代码质量", "加强算法思维"],
                    "learning_path": ["继续练习编程题目", "学习Python最佳实践"],
                    "detailed_feedback": f"测试完成，平均得分{total_score_avg:.1f}分"
                }
            
            PythonTestSession.update(
                total_score=total_score,
                status='completed',
                completed_at=datetime.now(),
                report=json.dumps(report)
            ).where(PythonTestSession.id == session.id).execute()
        
        return PythonSubmissionResponse(
            id=submission.id,
            session_id=submission.session_id,
            question_id=submission.question_id,
            user_code=submission.user_code,
            execution_result=basic_result.get("output", "") or basic_result.get("error", "执行完成"),
            test_results={"message": "已完成智能体评估", "score": final_score},
            review_result=review_result,
            score=final_score,
            is_passed=is_passed,
            submitted_at=submission.submitted_at.strftime('%Y-%m-%d %H:%M:%S')
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.exception(f"提交代码失败: {e}")
        raise HTTPException(status_code=500, detail=f"提交代码失败: {str(e)}")

@router.get("/report/{session_id}", response_model=TestReportResponse)
async def get_test_report(
    session_id: int,
    current_user: User = Depends(get_current_user)
):
    """获取测试报告"""
    try:
        session = PythonTestSession.get_or_none(
            (PythonTestSession.id == session_id) & (PythonTestSession.user_id == current_user.id)
        )
        
        if not session:
            raise HTTPException(status_code=404, detail="测试会话不存在")
        
        if session.status != 'completed':
            raise HTTPException(status_code=400, detail="测试尚未完成")
        
        # 获取智能体生成的报告 
        ai_report = json.loads(session.report) if session.report else {}
        
        # 如果智能体报告为空或不完整，重新生成
        if not ai_report or "overall_skill_level" not in ai_report:
            try:
                # 重新获取会话数据并生成报告
                all_submissions = list(PythonSubmission.select().where(PythonSubmission.session_id == session_id))
                session_data_for_agent = []
                
                for sub in all_submissions:
                    sub_question = PythonQuestion.get_by_id(sub.question_id)
                    review_data = json.loads(sub.review_result) if sub.review_result else {}
                    
                    session_data_for_agent.append({
                        "question_title": sub_question.title,
                        "difficulty": sub_question.difficulty,
                        "user_code": sub.user_code,
                        "score": sub.score,
                        "passed": sub.is_passed,
                        "review_result": review_data
                    })
                
                # 重新生成报告
                ai_report = await generate_python_session_report(session_data_for_agent)
                
                # 更新数据库
                PythonTestSession.update(
                    report=json.dumps(ai_report)
                ).where(PythonTestSession.id == session_id).execute()
                
            except Exception as regen_error:
                logging.error(f"重新生成报告失败: {regen_error}")
                ai_report = {"overall_skill_level": "中级", "detailed_feedback": "报告生成中遇到问题"}
        
        # 获取基础统计数据
        submissions = list(PythonSubmission.select().where(PythonSubmission.session_id == session_id))
        total_questions = len(submissions)
        passed_questions = sum(1 for s in submissions if s.is_passed)
        total_score = sum(s.score for s in submissions)
        average_score = total_score / total_questions if total_questions > 0 else 0
        
        # 构建符合Pydantic模型的报告数据
        report_data = {
            "session_id": session_id,
            "total_score": average_score,
            "questions_attempted": total_questions,
            "questions_passed": passed_questions,
            "difficulty_analysis": ai_report.get("difficulty_performance", {
                "difficulty_stats": {},
                "strongest_area": None,
                "weakest_area": None
            }),
            "skill_assessment": {
                "overall_skill_score": ai_report.get("skill_score", average_score),
                "skill_level": ai_report.get("overall_skill_level", "中级"),
                "skill_description": ai_report.get("detailed_feedback", "基于测试结果的评估")
            },
            "recommendations": ai_report.get("learning_path", [
                "继续练习Python编程题目",
                "重点关注代码质量和规范"
            ]),
            "detailed_results": []
        }
        
        # 构建详细结果
        for submission in submissions:
            question = PythonQuestion.get_by_id(submission.question_id)
            test_data = json.loads(submission.test_results) if submission.test_results else {}
            review_data = json.loads(submission.review_result) if submission.review_result else {}
            
            detailed_result = {
                "question_title": question.title,
                "difficulty": question.difficulty,
                "score": submission.score,
                "passed": submission.is_passed,
                "test_passed": test_data.get("passed_tests", 0),
                "test_total": test_data.get("total_tests", 0),
                "user_code": submission.user_code,
                "skill_level": review_data.get("skill_level", "未知"),
                "strengths": review_data.get("strengths", []),
                "improvements": review_data.get("weaknesses", [])
            }
            report_data["detailed_results"].append(detailed_result)
        
        return TestReportResponse(**report_data)
    except HTTPException:
        raise
    except Exception as e:
        logging.exception(f"获取测试报告失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取测试报告失败: {str(e)}")

async def generate_test_report(session_id: int, user_id: int) -> Dict[str, Any]:
    """生成基础测试报告（备用函数）"""
    try:
        # 获取所有提交记录
        submissions = list(PythonSubmission.select().where(PythonSubmission.session_id == session_id))
        
        if not submissions:
            raise ValueError("没有找到提交记录")
        
        # 统计数据
        total_questions = len(submissions)
        passed_questions = sum(1 for s in submissions if s.is_passed)
        total_score = sum(s.score for s in submissions)
        average_score = total_score / total_questions if total_questions > 0 else 0
        
        # 难度分析
        difficulty_stats = {}
        detailed_results = []
        
        for submission in submissions:
            question = PythonQuestion.get_by_id(submission.question_id)
            test_data = json.loads(submission.test_results) if submission.test_results else {}
            review_data = json.loads(submission.review_result) if submission.review_result else {}
            
            difficulty = question.difficulty
            if difficulty not in difficulty_stats:
                difficulty_stats[difficulty] = {"attempted": 0, "passed": 0, "scores": []}
            
            difficulty_stats[difficulty]["attempted"] += 1
            if submission.is_passed:
                difficulty_stats[difficulty]["passed"] += 1
            difficulty_stats[difficulty]["scores"].append(submission.score)
            
            # 详细结果
            detailed_results.append({
                "question_title": question.title,
                "difficulty": difficulty,
                "score": submission.score,
                "passed": submission.is_passed,
                "test_passed": test_data.get("passed_tests", 0),
                "test_total": test_data.get("total_tests", 0),
                "user_code": submission.user_code,
                "skill_level": review_data.get("skill_level", "未知"),
                "strengths": review_data.get("strengths", []),
                "improvements": review_data.get("weaknesses", [])
            })
        
        # 简化的技能评估（主要基于测试通过率和智能体评估）
        if average_score >= 80:
            skill_level = "高级"
            skill_description = "您在Python编程测试中表现优秀，代码质量较高。"
        elif average_score >= 60:
            skill_level = "中级"
            skill_description = "您具备一定的Python编程能力，在大部分测试中表现良好。"
        elif average_score >= 40:
            skill_level = "初级"
            skill_description = "您掌握了Python的基本语法，但需要加强练习。"
        else:
            skill_level = "入门"
            skill_description = "建议从Python基础语法开始系统学习。"
        
        # 收集智能体的建议
        all_suggestions = []
        for submission in submissions:
            if submission.review_result:
                review_data = json.loads(submission.review_result)
                suggestions = review_data.get("suggestions", [])
                all_suggestions.extend(suggestions)
        
        # 去重并取前5个建议
        unique_suggestions = list(dict.fromkeys(all_suggestions))[:5]
        if not unique_suggestions:
            unique_suggestions = [
                "继续练习Python编程题目",
                "重点关注代码质量和规范",
                "学习Python最佳实践"
            ]
        
        return {
            "session_id": session_id,
            "total_score": average_score,
            "questions_attempted": total_questions,
            "questions_passed": passed_questions,
            "overall_skill_level": skill_level,
            "skill_score": average_score,
            "difficulty_analysis": {
                "difficulty_stats": difficulty_stats,
                "strongest_area": max(difficulty_stats.keys(), key=lambda x: difficulty_stats[x].get("passed", 0) / max(difficulty_stats[x].get("attempted", 1), 1)) if difficulty_stats else None,
                "weakest_area": min(difficulty_stats.keys(), key=lambda x: difficulty_stats[x].get("passed", 0) / max(difficulty_stats[x].get("attempted", 1), 1)) if difficulty_stats else None
            },
            "skill_assessment": {
                "overall_skill_score": average_score,
                "skill_level": skill_level,
                "skill_description": skill_description
            },
            "recommendations": unique_suggestions,
            "detailed_results": detailed_results,
            "detailed_feedback": f"完成了{passed_questions}/{total_questions}道题目，平均得分{average_score:.1f}分。{skill_description}"
        }
    except Exception as e:
        logging.exception(f"生成测试报告失败: {e}")
        raise

@router.get("/sessions")
async def get_user_sessions(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user)
):
    """获取用户的测试会话列表"""
    try:
        sessions = (PythonTestSession.select()
                   .where(PythonTestSession.user_id == current_user.id)
                   .order_by(PythonTestSession.started_at.desc())
                   .paginate(page, size))
        
        result = []
        for session in sessions:
            questions = json.loads(session.questions) if session.questions else []
            result.append({
                "id": session.id,
                "session_name": session.session_name,
                "questions_count": len(questions),
                "total_score": session.total_score,
                "status": session.status,
                "started_at": session.started_at.strftime('%Y-%m-%d %H:%M:%S'),
                "completed_at": session.completed_at.strftime('%Y-%m-%d %H:%M:%S') if session.completed_at else None
            })
        
        return result
    except Exception as e:
        logging.exception(f"获取会话列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取会话列表失败: {str(e)}")