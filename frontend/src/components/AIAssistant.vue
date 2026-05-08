<template>
  <div class="ai-assistant">
    <!-- 浮动按钮 -->
    <div class="ai-fab" @click="toggleChat" :class="{ active: isOpen }">
      <el-icon v-if="!isOpen"><ChatDotRound /></el-icon>
      <el-icon v-else><Close /></el-icon>
    </div>

    <!-- 聊天窗口 -->
    <transition name="chat-slide">
      <div v-if="isOpen" class="chat-window">
        <!-- 头部 -->
        <div class="chat-header">
          <div class="header-title">
            <el-icon><Monitor /></el-icon>
            <span>AI法律助手</span>
          </div>
          <div class="header-actions">
            <el-tooltip content="清空对话" placement="top">
              <el-button type="text" @click="clearChat" :icon="Delete" circle size="small" />
            </el-tooltip>
            <el-tooltip content="最小化" placement="top">
              <el-button type="text" @click="isOpen = false" :icon="Minus" circle size="small" />
            </el-tooltip>
          </div>
        </div>

        <!-- 消息列表 -->
        <div class="chat-messages" ref="messagesRef">
          <div v-if="messages.length === 0" class="welcome-message">
            <el-icon class="welcome-icon"><Monitor /></el-icon>
            <h3>AI法律助手</h3>
            <p>我可以帮助您：</p>
            <ul>
              <li @click="sendQuickQuestion('请解释当前案件的法律要点')">
                <el-icon><Document /></el-icon>
                解释案件法律要点
              </li>
              <li @click="sendQuickQuestion('分析上传文件的主要内容')">
                <el-icon><Files /></el-icon>
                分析文件内容
              </li>
              <li @click="sendQuickQuestion('帮我检查表单填写是否完整')">
                <el-icon><Edit /></el-icon>
                检查表单完整性
              </li>
              <li @click="sendQuickQuestion('解释法律文书的各项条款')">
                <el-icon><Reading /></el-icon>
                解释文书条款
              </li>
            </ul>
          </div>

          <div v-for="(msg, index) in messages" :key="index"
               class="message-item" :class="msg.role">
            <div class="message-avatar">
              <el-icon v-if="msg.role === 'user'"><User /></el-icon>
              <el-icon v-else><Monitor /></el-icon>
            </div>
            <div class="message-content">
              <div class="message-text" v-html="formatMessage(msg.content)"></div>
              <div class="message-time">{{ msg.time }}</div>
            </div>
          </div>

          <!-- 加载中 -->
          <div v-if="loading" class="message-item assistant loading">
            <div class="message-avatar">
              <el-icon><Monitor /></el-icon>
            </div>
            <div class="message-content">
              <div class="typing-indicator">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        </div>

        <!-- 快捷操作 -->
        <div class="quick-actions" v-if="contextData">
          <el-tag
            v-if="contextData.company_info?.target_company"
            size="small"
            type="info"
            @click="sendQuickQuestion(`分析${contextData.company_info.target_company}的案件情况`)"
          >
            分析当前公司
          </el-tag>
          <el-tag
            v-if="contextData.defendants?.length"
            size="small"
            type="info"
            @click="sendQuickQuestion('分析被告信息，给出诉讼建议')"
          >
            分析被告信息
          </el-tag>
          <el-tag
            v-if="contextData.debt_info?.principal"
            size="small"
            type="info"
            @click="sendQuickQuestion('计算诉讼费用和保全费用')"
          >
            费用计算
          </el-tag>
        </div>

        <!-- 输入区域 -->
        <div class="chat-input">
          <el-input
            v-model="inputMessage"
            type="textarea"
            :rows="1"
            :autosize="{ minRows: 1, maxRows: 4 }"
            placeholder="输入法律问题..."
            @keydown.enter.exact.prevent="sendMessage"
            :disabled="loading"
          />
          <el-button
            type="primary"
            :icon="Promotion"
            circle
            @click="sendMessage"
            :loading="loading"
            :disabled="!inputMessage.trim()"
          />
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Delete, Minus, Promotion } from '@element-plus/icons-vue'
import api from '../api'

// 接收上下文数据
const props = defineProps({
  contextData: {
    type: Object,
    default: null
  },
  caseId: {
    type: String,
    default: ''
  }
})

// 状态
const isOpen = ref(false)
const messages = ref([])
const inputMessage = ref('')
const loading = ref(false)
const messagesRef = ref(null)

// 切换聊天窗口
function toggleChat() {
  isOpen.value = !isOpen.value
}

// 清空对话
function clearChat() {
  messages.value = []
}

// 发送消息
async function sendMessage() {
  if (!inputMessage.value.trim() || loading.value) return

  const userMessage = inputMessage.value.trim()
  inputMessage.value = ''

  // 添加用户消息
  messages.value.push({
    role: 'user',
    content: userMessage,
    time: new Date().toLocaleTimeString()
  })

  scrollToBottom()
  loading.value = true

  try {
    // 调用后端AI接口
    const response = await fetch('/api/ai/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: userMessage,
        history: messages.value.slice(-10), // 只发送最近10条消息
        context: props.contextData,
        case_id: props.caseId
      })
    })

    if (!response.ok) {
      throw new Error('请求失败')
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let assistantMessage = ''

    // 流式读取响应
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6)
          if (data === '[DONE]') continue

          try {
            const json = JSON.parse(data)
            if (json.content) {
              assistantMessage += json.content

              // 更新或添加助手消息
              const lastMsg = messages.value[messages.value.length - 1]
              if (lastMsg?.role === 'assistant') {
                lastMsg.content = assistantMessage
              } else {
                messages.value.push({
                  role: 'assistant',
                  content: assistantMessage,
                  time: new Date().toLocaleTimeString()
                })
              }
              scrollToBottom()
            }
          } catch (e) {
            // 忽略解析错误
          }
        }
      }
    }

    // 如果没有流式响应，使用普通响应
    if (!assistantMessage) {
      const result = await response.json()
      messages.value.push({
        role: 'assistant',
        content: result.message || '抱歉，我无法回答这个问题。',
        time: new Date().toLocaleTimeString()
      })
    }

  } catch (error) {
    ElMessage.error('AI服务暂时不可用，请稍后重试')
    messages.value.push({
      role: 'assistant',
      content: '抱歉，服务暂时不可用。请检查后端服务是否正常运行。',
      time: new Date().toLocaleTimeString()
    })
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

// 发送快捷问题
function sendQuickQuestion(question) {
  inputMessage.value = question
  sendMessage()
}

// 格式化消息（简单的Markdown支持）
function formatMessage(content) {
  if (!content) return ''

  return content
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br>')
}

// 滚动到底部
function scrollToBottom() {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}
</script>

<style scoped>
.ai-assistant {
  position: fixed;
  right: 24px;
  bottom: 24px;
  z-index: 1000;
}

.ai-fab {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4);
  transition: all 0.3s ease;
  color: white;
  font-size: 24px;
}

.ai-fab:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 24px rgba(102, 126, 234, 0.5);
}

.ai-fab.active {
  transform: rotate(180deg);
}

.chat-window {
  position: absolute;
  bottom: 72px;
  right: 0;
  width: 400px;
  height: 600px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chat-slide-enter-active,
.chat-slide-leave-active {
  transition: all 0.3s ease;
}

.chat-slide-enter-from,
.chat-slide-leave-to {
  opacity: 0;
  transform: translateY(20px) scale(0.95);
}

.chat-header {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  color: white;
  padding: 16px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 600;
  font-size: 16px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.header-actions .el-button {
  color: rgba(255, 255, 255, 0.8);
}

.header-actions .el-button:hover {
  color: white;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: #f8f9fa;
}

.welcome-message {
  text-align: center;
  padding: 40px 20px;
  color: #666;
}

.welcome-icon {
  font-size: 48px;
  color: #667eea;
  margin-bottom: 16px;
}

.welcome-message h3 {
  color: #1a1a2e;
  margin-bottom: 12px;
  font-size: 18px;
}

.welcome-message ul {
  list-style: none;
  padding: 0;
  margin-top: 20px;
}

.welcome-message li {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: white;
  border-radius: 10px;
  margin-bottom: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid #eee;
  font-size: 14px;
}

.welcome-message li:hover {
  border-color: #667eea;
  background: #f0f4ff;
  color: #667eea;
}

.welcome-message li .el-icon {
  font-size: 18px;
  color: #667eea;
}

.message-item {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.message-item.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.message-item.user .message-avatar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.message-item.assistant .message-avatar {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  color: white;
}

.message-content {
  max-width: 80%;
}

.message-text {
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.6;
}

.message-item.user .message-text {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-bottom-right-radius: 4px;
}

.message-item.assistant .message-text {
  background: white;
  color: #333;
  border-bottom-left-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.message-time {
  font-size: 11px;
  color: #999;
  margin-top: 4px;
  text-align: right;
}

.message-item.assistant .message-time {
  text-align: left;
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 12px 16px;
  background: white;
  border-radius: 12px;
  width: fit-content;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: #667eea;
  border-radius: 50%;
  animation: typing 1.4s infinite ease-in-out;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 80%, 100% {
    transform: scale(0.6);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

.quick-actions {
  padding: 8px 16px;
  background: white;
  border-top: 1px solid #eee;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.quick-actions .el-tag {
  cursor: pointer;
  transition: all 0.3s ease;
}

.quick-actions .el-tag:hover {
  background: #667eea;
  color: white;
  border-color: #667eea;
}

.chat-input {
  padding: 12px 16px;
  background: white;
  border-top: 1px solid #eee;
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.chat-input .el-textarea {
  flex: 1;
}

.chat-input .el-button {
  flex-shrink: 0;
}

/* 滚动条美化 */
.chat-messages::-webkit-scrollbar {
  width: 6px;
}

.chat-messages::-webkit-scrollbar-track {
  background: transparent;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: #ddd;
  border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-thumb:hover {
  background: #ccc;
}
</style>
