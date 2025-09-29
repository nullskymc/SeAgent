<template>
  <div class="python-test-container">
    <!-- 页面头部 -->
    <div class="header">
      <h1>Python 代码测试</h1>
      <p class="subtitle">通过5道精选题目评估您的Python编程水平</p>
    </div>

    <!-- 测试会话列表 -->
    <div v-if="currentView === 'sessions'" class="sessions-view">
      <div class="sessions-header">
        <h2>我的测试记录</h2>
        <el-button type="primary" @click="startNewTest" :loading="loading">
          <el-icon><Plus /></el-icon>开始新测试
        </el-button>
        <el-button type="warning" @click="regenerateQuestions" :loading="loading">
          <el-icon><Refresh /></el-icon>AI重新生成题目
        </el-button>
      </div>
      
      <div class="sessions-list">
        <el-card 
          v-for="session in sessions" 
          :key="session.id" 
          class="session-card"
          shadow="hover"
        >
          <div class="session-content">
            <div class="session-info">
              <h3>{{ session.session_name }}</h3>
              <p>题目数量: {{ session.questions_count }} | 总分: {{ session.total_score.toFixed(1) }}</p>
              <p>状态: 
                <el-tag :type="session.status === 'completed' ? 'success' : 'warning'">
                  {{ session.status === 'completed' ? '已完成' : '进行中' }}
                </el-tag>
              </p>
              <p class="date">开始时间: {{ session.started_at }}</p>
            </div>
            <div class="session-actions">
              <el-button 
                v-if="session.status === 'completed'" 
                @click="viewReport(session.id)"
                type="info"
              >
                查看报告
              </el-button>
              <el-button 
                v-else 
                @click="continueTest(session.id)"
                type="primary"
              >
                继续测试
              </el-button>
            </div>
          </div>
        </el-card>
      </div>
    </div>

    <!-- 测试进行中 -->
    <div v-if="currentView === 'testing'" class="testing-view">
      <el-card class="progress-card">
        <div class="progress-info">
          <span>题目 {{ currentQuestionIndex + 1 }} / {{ totalQuestions }}</span>
          <span>总分: {{ currentSession?.total_score?.toFixed(1) || 0 }}</span>
        </div>
        <el-progress 
          :percentage="((currentQuestionIndex + 1) / totalQuestions * 100)" 
          :stroke-width="8"
          color="#409EFF"
        />
      </el-card>

      <el-card class="question-card" v-if="currentQuestion">
        <template #header>
          <div class="question-header">
            <h2>{{ currentQuestion.title }}</h2>
            <el-tag :type="getDifficultyType(currentQuestion.difficulty)">
              难度: {{ getDifficultyText(currentQuestion.difficulty) }}
            </el-tag>
          </div>
        </template>
        
        <div class="question-content">
          <div class="description">
            <h3>题目描述</h3>
            <p>{{ currentQuestion.description }}</p>
          </div>
          
          <div class="example" v-if="currentQuestion.example_input">
            <h3>示例</h3>
            <el-descriptions :column="1" border>
              <el-descriptions-item label="输入">{{ currentQuestion.example_input }}</el-descriptions-item>
              <el-descriptions-item label="输出">{{ currentQuestion.example_output }}</el-descriptions-item>
            </el-descriptions>
          </div>
        </div>

        <div class="code-editor-section">
          <h3>代码编辑器</h3>
          <el-input
            v-model="userCode"
            type="textarea"
            :rows="15"
            placeholder="请在此处编写您的Python代码..."
            class="code-editor"
          />
          
          <div class="editor-actions">
            <el-button type="primary" @click="submitCode" :loading="submittingCode" :disabled="!userCode.trim()" size="large">
              <el-icon><Check /></el-icon>提交代码进行AI评估
            </el-button>
          </div>
        </div>

        <!-- 代码运行结果 -->
        <el-card v-if="codeOutput" class="output-card">
          <template #header>运行结果</template>
          <pre class="output">{{ codeOutput }}</pre>
        </el-card>
      </el-card>
    </div>

    <!-- 测试结果页面 -->
    <div v-if="currentView === 'result'" class="result-view">
      <el-card v-if="submissionResult" class="result-card">
        <template #header>
          <h2>题目完成</h2>
        </template>
        
        <div class="score-display">
          <el-progress 
            type="circle" 
            :percentage="submissionResult.score" 
            :width="120"
            :stroke-width="8"
            :color="submissionResult.is_passed ? '#67C23A' : '#F56C6C'"
          >
            <span class="score-text">{{ submissionResult.score.toFixed(1) }}分</span>
          </el-progress>
          <el-tag 
            :type="submissionResult.is_passed ? 'success' : 'danger'" 
            size="large"
            class="pass-status"
          >
            {{ submissionResult.is_passed ? '通过' : '未通过' }}
          </el-tag>
        </div>

        <!-- 测试结果详情 -->
        <el-collapse v-if="submissionResult.review_result" class="result-details">
          <!-- 代码审查结果 -->
          <el-collapse-item title="智能代码审查" name="review">
            <div class="ai-review-section">
              <div class="review-header">
                <h4>AI专家评估</h4>
                <div class="review-scores">
                  <el-statistic 
                    title="代码质量" 
                    :value="submissionResult.review_result.quality_score || 0" 
                    suffix="/10"
                  />
                  <el-tag 
                    :type="getSkillLevelType(submissionResult.review_result.skill_level)"
                    size="large"
                  >
                    {{ submissionResult.review_result.skill_level || '未知' }}
                  </el-tag>
                </div>
              </div>

              <div class="review-content">
                <!-- 优点 -->
                <div v-if="submissionResult.review_result.strengths?.length" class="review-strengths">
                  <h5>代码亮点</h5>
                  <el-tag 
                    v-for="strength in submissionResult.review_result.strengths" 
                    :key="strength"
                    type="success"
                    class="review-tag"
                  >
                    {{ strength }}
                  </el-tag>
                </div>

                <!-- 不足 -->
                <div v-if="submissionResult.review_result.weaknesses?.length" class="review-weaknesses">
                  <h5>需要改进</h5>
                  <el-tag 
                    v-for="weakness in submissionResult.review_result.weaknesses" 
                    :key="weakness"
                    type="warning"
                    class="review-tag"
                  >
                    {{ weakness }}
                  </el-tag>
                </div>

                <!-- 改进建议 -->
                <div v-if="submissionResult.review_result.suggestions?.length" class="review-suggestions">
                  <h5>改进建议</h5>
                  <ul>
                    <li v-for="suggestion in submissionResult.review_result.suggestions" :key="suggestion">
                      {{ suggestion }}
                    </li>
                  </ul>
                </div>

                <!-- 学习建议 -->
                <div v-if="submissionResult.review_result.learning_recommendations?.length" class="review-learning">
                  <h5>学习建议</h5>
                  <ul>
                    <li v-for="rec in submissionResult.review_result.learning_recommendations" :key="rec">
                      {{ rec }}
                    </li>
                  </ul>
                </div>

                <!-- 详细分析 -->
                <div v-if="submissionResult.review_result.detailed_analysis" class="review-detailed">
                  <h5>详细分析</h5>
                  <div class="detailed-text">
                    {{ submissionResult.review_result.detailed_analysis }}
                  </div>
                </div>
              </div>
            </div>
          </el-collapse-item>
        </el-collapse>

        <div class="result-actions">
          <el-button v-if="hasNextQuestion" type="primary" @click="nextQuestion">
            下一题 <el-icon><ArrowRight /></el-icon>
          </el-button>
          <el-button v-else type="success" @click="viewFinalReport">
            查看完整报告
          </el-button>
        </div>
      </el-card>
    </div>

    <!-- 测试报告页面 -->
    <div v-if="currentView === 'report'" class="report-view">
      <el-card v-if="testReport" class="report-card">
        <template #header>
          <h1>Python 技能评估报告</h1>
        </template>
        
        <el-row :gutter="20" class="report-summary">
          <el-col :span="12">
            <el-card class="summary-card">
              <template #header>总体表现</template>
              <el-descriptions :column="1" border>
                <el-descriptions-item label="总分">{{ testReport.total_score.toFixed(1) }}</el-descriptions-item>
                <el-descriptions-item label="通过题目">
                  {{ testReport.questions_passed }} / {{ testReport.questions_attempted }}
                </el-descriptions-item>
                <el-descriptions-item label="技能等级">
                  <el-tag type="primary">{{ testReport.skill_assessment.skill_level }}</el-tag>
                </el-descriptions-item>
              </el-descriptions>
            </el-card>
          </el-col>

          <el-col :span="12">
            <el-card class="summary-card">
              <template #header>技能描述</template>
              <p>{{ testReport.skill_assessment.skill_description }}</p>
            </el-card>
          </el-col>
        </el-row>

        <el-card class="difficulty-card">
          <template #header>难度表现分析</template>
          <div class="difficulty-chart">
            <div 
              v-for="(stats, difficulty) in testReport.difficulty_analysis.difficulty_stats" 
              :key="difficulty" 
              class="difficulty-item"
            >
              <span class="difficulty-label">难度{{ difficulty }}</span>
              <el-progress 
                :percentage="(stats.passed / stats.attempted * 100)" 
                :format="() => `${stats.passed}/${stats.attempted}`"
              />
            </div>
          </div>
        </el-card>

        <el-card class="recommendations-card">
          <template #header>改进建议</template>
          <ul class="recommendation-list">
            <li v-for="recommendation in testReport.recommendations" :key="recommendation">
              {{ recommendation }}
            </li>
          </ul>
        </el-card>

        <el-card class="detailed-results-card">
          <template #header>详细结果</template>
          <el-table :data="testReport.detailed_results" style="width: 100%">
            <el-table-column prop="question_title" label="题目" />
            <el-table-column prop="difficulty" label="难度" width="80" />
            <el-table-column prop="score" label="得分" width="80">
              <template #default="scope">
                {{ scope.row.score.toFixed(1) }}
              </template>
            </el-table-column>
            <el-table-column prop="passed" label="状态" width="80">
              <template #default="scope">
                <el-tag :type="scope.row.passed ? 'success' : 'danger'">
                  {{ scope.row.passed ? '通过' : '未通过' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="skill_level" label="AI评级" width="100">
              <template #default="scope">
                <el-tag :type="getSkillLevelType(scope.row.skill_level)">
                  {{ scope.row.skill_level || '未知' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>

        <!-- AI详细反馈 -->
        <el-card v-if="testReport.detailed_feedback" class="ai-feedback-card">
          <template #header>AI专家点评</template>
          <div class="ai-feedback">
            {{ testReport.detailed_feedback }}
          </div>
        </el-card>

        <div class="report-actions">
          <el-button @click="backToSessions" type="primary">
            返回测试列表
          </el-button>
          <el-button @click="startNewTest" type="success">
            开始新测试
          </el-button>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  Plus, VideoPlay, Check, ArrowRight, 
  Close, Refresh
} from '@element-plus/icons-vue'
import api from '@/services/api'

export default {
  name: 'PythonTest',
  components: {
    Plus, VideoPlay, Check, ArrowRight, Close, Refresh
  },
  setup() {
    // 响应式数据
    const currentView = ref('sessions') // sessions, testing, result, report
    const loading = ref(false)
    const runningCode = ref(false)
    const submittingCode = ref(false)
    
    const sessions = ref([])
    const currentSession = ref(null)
    const currentQuestion = ref(null)
    const currentQuestionIndex = ref(0)
    const totalQuestions = ref(5)
    const userCode = ref('')
    const codeOutput = ref('')
    
    const submissionResult = ref(null)
    const testReport = ref(null)
    const hasNextQuestion = computed(() => currentQuestionIndex.value < totalQuestions.value - 1)

    // 方法
    const loadSessions = async () => {
      try {
        loading.value = true
        const response = await api.get('/python-test/sessions')
        sessions.value = response
      } catch (error) {
        console.error('加载会话失败:', error)
        ElMessage.error('加载测试记录失败')
      } finally {
        loading.value = false
      }
    }

    const startNewTest = async () => {
      try {
        loading.value = true
        
        // 先初始化题目（使用智能体生成）
        try {
          const initResponse = await api.post('/python-test/init-questions')
          console.log('题目初始化结果:', initResponse)
        } catch (error) {
          // 题目可能已经存在，忽略错误
          console.log('题目初始化信息:', error.response?.data?.detail || '题目可能已存在')
        }
        
        // 创建新的测试会话
        const response = await api.post('/python-test/sessions', {
          session_name: `Python测试 ${new Date().toLocaleString()}`
        })
        
        currentSession.value = response
        currentQuestionIndex.value = 0
        await loadCurrentQuestion()
        currentView.value = 'testing'
      } catch (error) {
        console.error('开始测试失败:', error)
        ElMessage.error('开始测试失败')
      } finally {
        loading.value = false
      }
    }

    const continueTest = async (sessionId) => {
      try {
        loading.value = true
        
        const response = await api.get(`/python-test/sessions/${sessionId}`)
        currentSession.value = response
        currentQuestionIndex.value = response.current_question_index
        await loadCurrentQuestion()
        currentView.value = 'testing'
      } catch (error) {
        console.error('继续测试失败:', error)
        ElMessage.error('继续测试失败')
      } finally {
        loading.value = false
      }
    }

    const loadCurrentQuestion = async () => {
      try {
        if (!currentSession.value || !currentSession.value.questions) return
        
        const questionId = currentSession.value.questions[currentQuestionIndex.value]
        const response = await api.get(`/python-test/questions/${questionId}`)
        currentQuestion.value = response
        
        // 加载模板代码
        if (response.template_code) {
          userCode.value = response.template_code
        } else {
          userCode.value = ''
        }
        
        codeOutput.value = ''
      } catch (error) {
        console.error('加载题目失败:', error)
        ElMessage.error('加载题目失败')
      }
    }

    const submitCode = async () => {
      try {
        submittingCode.value = true
        
        const response = await api.post('/python-test/submit', {
          session_id: currentSession.value.id,
          question_id: currentQuestion.value.id,
          user_code: userCode.value
        })
        
        submissionResult.value = response
        currentView.value = 'result'
      } catch (error) {
        console.error('提交代码失败:', error)
        ElMessage.error('提交代码失败')
      } finally {
        submittingCode.value = false
      }
    }

    const nextQuestion = () => {
      currentQuestionIndex.value++
      loadCurrentQuestion()
      currentView.value = 'testing'
      userCode.value = ''
      codeOutput.value = ''
      submissionResult.value = null
    }

    const viewFinalReport = async () => {
      try {
        loading.value = true
        
        const response = await api.get(`/python-test/report/${currentSession.value.id}`)
        testReport.value = response
        currentView.value = 'report'
      } catch (error) {
        console.error('加载报告失败:', error)
        ElMessage.error('加载测试报告失败')
      } finally {
        loading.value = false
      }
    }

    const viewReport = async (sessionId) => {
      try {
        loading.value = true
        
        const response = await api.get(`/python-test/report/${sessionId}`)
        testReport.value = response
        currentView.value = 'report'
      } catch (error) {
        console.error('加载报告失败:', error)
        ElMessage.error('加载测试报告失败')
      } finally {
        loading.value = false
      }
    }

    const backToSessions = () => {
      currentView.value = 'sessions'
      loadSessions()
    }

    const getDifficultyText = (difficulty) => {
      const levels = { 1: '⭐ 入门', 2: '⭐⭐ 初级', 3: '⭐⭐⭐ 中级', 4: '⭐⭐⭐⭐ 高级', 5: '⭐⭐⭐⭐⭐ 专家' }
      return levels[difficulty] || '未知'
    }

    const getDifficultyType = (difficulty) => {
      const types = { 1: 'info', 2: 'success', 3: 'warning', 4: 'danger', 5: 'danger' }
      return types[difficulty] || 'info'
    }

    const getSkillLevelType = (skillLevel) => {
      const types = { 
        '入门': 'info', 
        '初级': 'success', 
        '中级': 'warning', 
        '高级': 'danger',
        '专家': 'danger'
      }
      return types[skillLevel] || 'info'
    }

    const regenerateQuestions = async () => {
      try {
        loading.value = true
        ElMessage.info('正在使用AI重新生成题目，请稍候...')
        
        const response = await api.post('/python-test/regenerate-questions')
        
        ElMessage.success(response.message || '题目重新生成成功！')
        console.log('题目重新生成结果:', response)
        
        // 刷新会话列表
        await loadSessions()
        
      } catch (error) {
        console.error('重新生成题目失败:', error)
        ElMessage.error('重新生成题目失败，请重试')
      } finally {
        loading.value = false
      }
    }

    // 生命周期
    onMounted(() => {
      loadSessions()
    })

    return {
      currentView,
      loading,
      submittingCode,
      sessions,
      currentSession,
      currentQuestion,
      currentQuestionIndex,
      totalQuestions,
      userCode,
      codeOutput,
      submissionResult,
      testReport,
      hasNextQuestion,
      
      // 方法
      startNewTest,
      continueTest,
      loadCurrentQuestion,
      submitCode,
      nextQuestion,
      viewFinalReport,
      viewReport,
      backToSessions,
      getDifficultyText,
      getDifficultyType,
      getSkillLevelType,
      regenerateQuestions
    }
  }
}
</script>

<style scoped>
.python-test-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.header {
  text-align: center;
  margin-bottom: 30px;
}

.header h1 {
  color: var(--el-text-color-primary);
  margin-bottom: 10px;
}

.subtitle {
  color: var(--el-text-color-regular);
  font-size: 1.1em;
}

/* 会话列表样式 */
.sessions-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.sessions-list {
  display: grid;
  gap: 15px;
}

.session-card {
  margin-bottom: 10px;
}

.session-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.session-info h3 {
  margin: 0 0 10px 0;
  color: var(--el-text-color-primary);
}

.session-info p {
  margin: 5px 0;
  color: var(--el-text-color-regular);
}

.date {
  font-size: 0.9em;
  color: var(--el-text-color-secondary);
}

/* 测试进行中样式 */
.progress-card {
  margin-bottom: 20px;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 15px;
  font-weight: bold;
  color: var(--el-text-color-primary);
}

.question-card {
  margin-bottom: 20px;
}

.question-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.question-header h2 {
  color: var(--el-text-color-primary);
  margin: 0;
}

.question-content {
  margin-bottom: 20px;
}

.description, .example {
  margin-bottom: 20px;
}

.code-editor {
  margin-bottom: 15px;
}

.code-editor :deep(textarea) {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 14px;
  line-height: 1.5;
}

.editor-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.output-card {
  margin-top: 20px;
}

.output {
  font-family: monospace;
  white-space: pre-wrap;
  margin: 0;
  background: var(--el-fill-color-light);
  padding: 10px;
  border-radius: 4px;
  color: var(--el-text-color-primary);
}

/* 结果页面样式 */
.result-card {
  margin-bottom: 20px;
}

.score-display {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 30px;
  margin: 30px 0;
}

.score-text {
  font-weight: bold;
  font-size: 16px;
}

.pass-status {
  font-size: 16px;
  padding: 8px 16px;
}

.result-details {
  margin: 25px 0;
}

.test-summary {
  display: flex;
  gap: 40px;
  margin-bottom: 20px;
}

.test-cases {
  display: grid;
  gap: 10px;
}

.test-case {
  margin-bottom: 10px;
}

.test-case.passed {
  border-left: 4px solid var(--el-color-success);
}

.test-case.failed {
  border-left: 4px solid var(--el-color-danger);
}

.test-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
  margin-bottom: 10px;
}

.test-details p {
  margin: 5px 0;
  font-family: monospace;
  font-size: 0.9em;
}

.error {
  color: var(--el-color-danger);
  font-weight: bold;
}

.skill-assessment {
  display: flex;
  gap: 40px;
  margin-bottom: 20px;
}

.result-actions {
  display: flex;
  gap: 10px;
  justify-content: center;
  margin-top: 30px;
}

/* 报告页面样式 */
.report-card {
  margin-bottom: 20px;
}

.report-summary {
  margin-bottom: 30px;
}

.summary-card {
  margin-bottom: 20px;
}

.difficulty-card, .recommendations-card, .detailed-results-card, .ai-feedback-card {
  margin-bottom: 20px;
}

.ai-review-section {
  margin-bottom: 20px;
}

.review-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.review-scores {
  display: flex;
  gap: 20px;
  align-items: center;
}

.review-content > div {
  margin-bottom: 15px;
}

.review-content h5 {
  margin: 0 0 10px 0;
  font-weight: bold;
  color: var(--el-text-color-primary);
}

.review-tag {
  margin: 2px 5px 2px 0;
}

.review-suggestions ul, .review-learning ul {
  margin: 0;
  padding-left: 20px;
}

.review-suggestions li, .review-learning li {
  margin-bottom: 5px;
  line-height: 1.4;
}

.review-detailed .detailed-text {
  background: var(--el-fill-color-light);
  padding: 15px;
  border-radius: 4px;
  line-height: 1.6;
  color: var(--el-text-color-primary);
}

.ai-feedback {
  line-height: 1.6;
  color: var(--el-text-color-primary);
  background: var(--el-fill-color-extra-light);
  padding: 15px;
  border-radius: 4px;
  border-left: 4px solid var(--el-color-primary);
}

.recommendations-card, .detailed-results-card {
  margin-bottom: 20px;
}

.difficulty-chart {
  display: grid;
  gap: 15px;
}

.difficulty-item {
  display: flex;
  align-items: center;
  gap: 15px;
}

.difficulty-label {
  min-width: 80px;
  font-weight: bold;
  color: var(--el-text-color-primary);
}

.recommendation-list {
  list-style: none;
  padding: 0;
}

.recommendation-list li {
  padding: 10px 0;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.recommendation-list li:last-child {
  border-bottom: none;
}

.report-actions {
  display: flex;
  gap: 10px;
  justify-content: center;
  margin-top: 30px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .python-test-container {
    padding: 10px;
  }
  
  .session-content {
    flex-direction: column;
    gap: 15px;
  }
  
  .report-summary {
    flex-direction: column;
  }
  
  .difficulty-item {
    flex-direction: column;
    align-items: stretch;
  }
  
  .score-display {
    flex-direction: column;
    gap: 15px;
  }
  
  .test-summary, .skill-assessment {
    flex-direction: column;
    gap: 20px;
  }
}
</style>