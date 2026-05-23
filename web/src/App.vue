<template>
  <div class="flex flex-col h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 relative overflow-hidden">
    <!-- 背景装饰 -->
    <div class="absolute inset-0 overflow-hidden pointer-events-none">
      <div class="absolute top-20 left-10 w-96 h-96 bg-gradient-to-br from-blue-400/10 to-purple-400/10 rounded-full blur-3xl"></div>
      <div class="absolute bottom-20 right-10 w-80 h-80 bg-gradient-to-br from-indigo-400/10 to-pink-400/10 rounded-full blur-3xl"></div>
    </div>
    
    <!-- 顶部导航 -->
    <header class="bg-white/70 backdrop-blur-xl border-b border-gray-200/50 px-6 py-4 sticky top-0 z-10 shadow-sm">
      <div class="max-w-5xl mx-auto flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl flex items-center justify-center overflow-hidden shadow-xl shadow-blue-500/30 bg-gradient-to-br from-blue-500 via-indigo-500 to-purple-600 relative">
            <div class="absolute inset-0 bg-white/10 rounded-xl"></div>
            <img src="/src/resources/logo.png" alt="FastAgent" class="w-full h-full object-contain p-1.5 relative z-10" />
          </div>
          <div>
            <h1 class="text-xl font-bold bg-gradient-to-r from-gray-800 to-gray-600 bg-clip-text text-transparent">FastAgent</h1>
            <p class="text-xs text-gray-500">智能助手</p>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <!-- 历史记录按钮 -->
          <button 
            @click="toggleHistory" 
            class="text-gray-500 hover:text-blue-600 hover:bg-blue-50 transition-all duration-200 p-2.5 rounded-xl"
            title="历史对话"
          >
            <i class="fa fa-history text-lg"></i>
          </button>
          <!-- 清空对话按钮 -->
          <button 
            @click="clearChat" 
            class="text-gray-500 hover:text-red-600 hover:bg-red-50 transition-all duration-200 p-2.5 rounded-xl"
            title="清空对话"
          >
            <i class="fa fa-trash-o text-lg"></i>
          </button>
          <!-- 分隔线 -->
          <div class="w-px h-8 bg-gray-200 mx-2"></div>
          <!-- 登录状态 -->
          <div v-if="isLoggedIn" class="flex items-center gap-3">
            <div class="w-9 h-9 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center text-white font-semibold text-sm shadow-lg shadow-blue-500/30">
              {{ user.username.charAt(0).toUpperCase() }}
            </div>
            <span class="text-sm font-medium text-gray-700 hidden sm:inline">{{ user.username }}</span>
            <button 
              @click="logout" 
              class="text-gray-500 hover:text-red-600 hover:bg-red-50 transition-all duration-200 p-2.5 rounded-xl"
              title="退出登录"
            >
              <i class="fa fa-sign-out text-lg"></i>
            </button>
          </div>
          <!-- 未登录状态 -->
          <div v-else class="flex items-center gap-2">
            <button 
              @click="openAuthDialog(true)" 
              class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-200 rounded-xl hover:bg-gray-50 hover:border-gray-300 transition-all duration-200 shadow-sm"
            >
              登录
            </button>
            <button 
              @click="openAuthDialog(false)" 
              class="px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl hover:from-blue-700 hover:to-indigo-700 transition-all duration-200 shadow-lg shadow-blue-500/30"
            >
              注册
            </button>
          </div>
        </div>
      </div>
    </header>
    
    <!-- 登录/注册对话框 -->
    <AuthDialog 
      :is-visible="authDialogVisible" 
      :is-login="authDialogIsLogin"
      @close="closeAuthDialog"
      @login-success="handleLoginSuccess"
    />

    <!-- 历史记录侧边栏 -->
    <div v-if="historyDialogVisible" class="fixed inset-y-0 left-0 bg-white/95 backdrop-blur-xl shadow-2xl z-50 w-[380px] max-w-[90vw] flex flex-col transform transition-all duration-300 ease-out">
      <div class="flex items-center justify-between p-6 border-b border-gray-100">
        <div>
          <h2 class="text-xl font-bold text-gray-800">历史对话</h2>
          <p class="text-xs text-gray-500 mt-1">{{ sessions.length }} 条记录</p>
        </div>
        <button 
          @click="historyDialogVisible = false" 
          class="text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-all duration-200 p-2.5 rounded-xl"
        >
          <i class="fa fa-times text-lg"></i>
        </button>
      </div>
      <div class="flex-1 overflow-y-auto p-4 space-y-3">
        <!-- 加载状态 -->
        <div v-if="isLoadingHistory" class="flex items-center justify-center h-40">
          <div class="loading-dots">
            <span></span><span></span><span></span>
          </div>
        </div>
        <!-- 空状态 -->
        <div v-else-if="sessions.length === 0" class="flex flex-col items-center justify-center h-40 text-gray-400">
          <div class="w-16 h-16 bg-gray-100 rounded-2xl flex items-center justify-center mb-3">
            <i class="fa fa-comments-o text-3xl text-gray-300"></i>
          </div>
          <p class="text-sm">暂无历史对话</p>
          <p class="text-xs text-gray-400 mt-1">开始对话后将自动保存</p>
        </div>
        <!-- 会话列表 -->
        <div v-else class="space-y-3">
          <div 
            v-for="session in sessions" 
            :key="session.session_id"
            class="group bg-gradient-to-br from-gray-50 to-white rounded-2xl p-4 hover:from-blue-50 hover:to-indigo-50 transition-all duration-200 cursor-pointer border border-gray-100 hover:border-blue-200"
            @click="loadSession(session.session_id)"
          >
            <div class="flex items-start justify-between gap-3">
              <div class="flex-1 min-w-0">
                <h3 class="font-medium text-gray-800 truncate group-hover:text-blue-600 transition-colors">{{ session.title || '未命名对话' }}</h3>
                <p class="text-xs text-gray-500 mt-1.5">{{ session.message_count }} 条消息</p>
              </div>
              <span class="text-xs text-gray-400 whitespace-nowrap">{{ formatTime(session.updated_at) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
    <!-- 背景遮罩 -->
    <div v-if="historyDialogVisible" class="fixed inset-0 bg-gray-900/20 backdrop-blur-sm z-40 transition-opacity duration-300" @click="historyDialogVisible = false"></div>

    <!-- 主内容区 -->
    <main class="flex-1 overflow-hidden flex flex-col max-w-5xl mx-auto w-full relative">
      <!-- 聊天区域 -->
      <div 
        ref="chatContainer" 
        class="flex-1 overflow-y-auto p-6 space-y-6 scroll-smooth"
      >
        <!-- 空状态 -->
        <div v-if="messages.length === 0" class="flex flex-col items-center justify-center h-full min-h-[60vh] text-gray-400 space-y-6">
          <div class="w-24 h-24 bg-gradient-to-br from-blue-100 to-indigo-100 rounded-3xl flex items-center justify-center shadow-xl shadow-blue-500/10">
            <i class="fa fa-comments text-4xl text-blue-500"></i>
          </div>
          <div class="text-center space-y-2">
            <p v-if="isLoggedIn" class="text-lg font-medium text-gray-600">开始一段新的对话吧</p>
            <div v-else class="space-y-3">
              <p class="text-sm text-gray-500">登录后即可使用智能对话功能</p>
              <button 
                @click="openAuthDialog(true)" 
                class="px-6 py-3 text-sm font-medium text-white bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl hover:from-blue-700 hover:to-indigo-700 transition-all duration-200 shadow-lg shadow-blue-500/30"
              >
                立即登录
              </button>
            </div>
          </div>
          <!-- 功能标签 -->
          <div v-if="isLoggedIn" class="space-y-3">
            <div class="flex flex-wrap justify-center gap-2 text-xs">
              <span class="px-4 py-2 bg-white/80 backdrop-blur rounded-full shadow-sm text-gray-600 hover:bg-blue-50 hover:text-blue-600 transition-all cursor-pointer">💬 智能问答</span>
              <span class="px-4 py-2 bg-white/80 backdrop-blur rounded-full shadow-sm text-gray-600 hover:bg-purple-50 hover:text-purple-600 transition-all cursor-pointer">🖼️ 图片分析</span>
              <span class="px-4 py-2 bg-white/80 backdrop-blur rounded-full shadow-sm text-gray-600 hover:bg-green-50 hover:text-green-600 transition-all cursor-pointer">🗄️ 数据查询</span>
            </div>
            <div class="flex flex-wrap justify-center gap-2 text-xs">
              <span class="px-4 py-2 bg-white/80 backdrop-blur rounded-full shadow-sm text-gray-600 hover:bg-orange-50 hover:text-orange-600 transition-all cursor-pointer">🔍 信息检索</span>
              <span class="px-4 py-2 bg-white/80 backdrop-blur rounded-full shadow-sm text-gray-600 hover:bg-pink-50 hover:text-pink-600 transition-all cursor-pointer">📍 位置导航</span>
              <span class="px-4 py-2 bg-white/80 backdrop-blur rounded-full shadow-sm text-gray-600 hover:bg-teal-50 hover:text-teal-600 transition-all cursor-pointer">📋 事务处理</span>
            </div>
          </div>
        </div>

        <!-- 消息列表 -->
        <transition-group name="message" tag="div" class="space-y-6">
          <div 
            v-for="(message, index) in messages" 
            :key="index"
            class="message flex animate-slide-up" 
            :class="message.role === 'user' ? 'justify-end' : 'justify-start'"
          >
            <!-- AI头像 -->
            <div v-if="message.role === 'assistant'" class="mr-4 flex-shrink-0">
              <div class="w-10 h-10 rounded-full flex items-center justify-center overflow-hidden shadow-xl shadow-blue-500/30 bg-gradient-to-br from-blue-500 via-indigo-500 to-purple-600 relative animate-float">
                <div class="absolute inset-0 bg-white/20 rounded-full"></div>
                <img src="/src/resources/logo.png" alt="AI" class="w-full h-full object-contain p-1.5 relative z-10" />
              </div>
            </div>

            <!-- 消息气泡 -->
            <div 
              class="max-w-[70%] rounded-2xl px-5 py-4 shadow-lg" 
              :class="message.role === 'user' 
                ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-br-md shadow-blue-500/30' 
                : 'bg-white/95 backdrop-blur text-gray-800 rounded-bl-md shadow-gray-200/50 border border-gray-100'"
            >
              <!-- Agent类型标签 -->
              <div v-if="message.role === 'assistant' && message.agentType" class="flex items-center gap-2 mb-3">
                <span class="text-xs px-2.5 py-1 bg-gradient-to-r from-blue-50 to-indigo-50 text-blue-600 rounded-lg font-medium">
                  {{ getAgentLabel(message.agentType) }}
                </span>
              </div>

              <!-- 图片标记 -->
              <div v-if="message.role === 'user' && message.imageCount > 0" class="flex items-center gap-2 mb-3 text-blue-100">
                <i class="fa fa-image"></i>
                <span class="text-sm">{{ message.imageCount }}张图片</span>
              </div>

              <!-- 消息内容 -->
              <div class="whitespace-pre-wrap text-[15px] leading-relaxed">{{ message.content }}</div>
            </div>

            <!-- 用户头像 -->
            <div v-if="message.role === 'user'" class="ml-4 flex-shrink-0">
              <div class="w-10 h-10 bg-gradient-to-br from-gray-400 to-gray-500 rounded-2xl flex items-center justify-center shadow-lg">
                <i class="fa fa-user text-white text-sm"></i>
              </div>
            </div>
          </div>
        </transition-group>

        <!-- 加载状态 -->
        <div v-if="isProcessing" class="message flex justify-start animate-slide-up">
          <div class="mr-4 flex-shrink-0">
            <div class="w-10 h-10 rounded-full flex items-center justify-center overflow-hidden shadow-xl shadow-blue-500/40 bg-gradient-to-br from-blue-500 via-indigo-500 to-purple-600 relative animate-pulse-slow">
              <div class="absolute inset-0 bg-white/25 rounded-full"></div>
              <img src="/src/resources/logo.png" alt="AI" class="w-full h-full object-contain p-1.5 relative z-10" />
            </div>
          </div>
          <div class="bg-white/95 backdrop-blur rounded-2xl rounded-bl-md shadow-lg border border-gray-100 px-6 py-4">
            <div class="loading-dots">
              <span></span><span></span><span></span>
            </div>
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="bg-white/80 backdrop-blur-xl border-t border-gray-200/50 p-5 shadow-[0_-4px_20px_rgba(0,0,0,0.05)]">
        <div class="max-w-5xl mx-auto">
          <!-- 图片预览 -->
          <div v-if="selectedImages.length > 0" class="flex gap-3 mb-4 flex-wrap">
            <div 
              v-for="(src, index) in selectedImages" 
              :key="index"
              class="relative group"
            >
              <img 
                :src="src" 
                class="w-16 h-16 object-cover rounded-xl border-2 border-gray-200 group-hover:border-blue-400 transition-all duration-200 shadow-md"
              />
              <button 
                @click="removeImage(index)"
                class="absolute -top-2 -right-2 w-6 h-6 bg-red-500 text-white rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all duration-200 shadow-lg hover:bg-red-600 hover:scale-110"
              >
                <i class="fa fa-times text-xs"></i>
              </button>
            </div>
          </div>

          <!-- 输入框 -->
          <div class="flex gap-3 items-end">
            <!-- 图片上传 -->
            <button 
              @click="handleButtonClick(triggerImageUpload)"
              :disabled="!isLoggedIn"
              class="p-3 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-xl transition-all duration-200 flex-shrink-0 disabled:opacity-50 disabled:cursor-not-allowed"
              :class="{ 'text-blue-600 bg-blue-50': selectedImages.length > 0 }"
              title="上传图片"
            >
              <i class="fa fa-image text-lg"></i>
              <span v-if="selectedImages.length > 0" class="ml-1 text-xs font-semibold">{{ selectedImages.length }}</span>
              <input 
                ref="imageInput" 
                type="file" 
                accept="image/*" 
                multiple 
                class="hidden" 
                @change="handleImageUpload"
              />
            </button>

            <!-- 文件上传 -->
            <button 
              @click="handleButtonClick(triggerFileUpload)"
              :disabled="!isLoggedIn"
              class="p-3 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-xl transition-all duration-200 flex-shrink-0 disabled:opacity-50 disabled:cursor-not-allowed"
              title="上传文件"
            >
              <i class="fa fa-file text-lg"></i>
              <input 
                ref="fileInput" 
                type="file" 
                class="hidden" 
                @change="handleFileUpload"
              />
            </button>

            <!-- 语音输入 -->
            <button 
              @click="handleButtonClick(toggleVoiceRecording)"
              :disabled="!isLoggedIn"
              class="p-3 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-xl transition-all duration-200 flex-shrink-0 disabled:opacity-50 disabled:cursor-not-allowed"
              :class="{ 'text-red-500 bg-red-50 animate-pulse': isRecording }"
              title="语音输入"
            >
              <i class="fa fa-microphone text-lg"></i>
            </button>

            <!-- 输入框 -->
            <div class="flex-1 relative">
              <textarea 
                v-model="userInput" 
                rows="1" 
                :disabled="!isLoggedIn"
                class="w-full bg-gray-50/80 border-2 border-gray-200 rounded-2xl px-5 py-4 pr-14 focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 focus:bg-white transition-all resize-none text-[15px] disabled:bg-gray-100 disabled:cursor-not-allowed shadow-sm"
                :placeholder="isLoggedIn ? '输入您的问题...' : '请先登录后使用'"
                @keydown.enter.prevent="sendMessage"
                @input="autoResize"
                @click="handleInputClick"
                ref="textareaRef"
              ></textarea>
              <div class="absolute right-3 bottom-3 text-xs text-gray-400">
                {{ userInput.length > 0 ? userInput.length : '' }}
              </div>
            </div>

            <!-- 发送按钮 -->
            <button 
              @click="sendMessage"
              :disabled="!isLoggedIn || isProcessing || (!userInput.trim() && selectedImages.length === 0)"
              class="p-4 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 disabled:from-gray-300 disabled:to-gray-300 text-white rounded-2xl transition-all duration-200 shadow-lg disabled:shadow-none flex-shrink-0 hover:scale-105 disabled:hover:scale-100 active:scale-95"
            >
              <i v-if="!isProcessing" class="fa fa-paper-plane text-lg"></i>
              <i v-else class="fa fa-spinner fa-spin text-lg"></i>
            </button>
          </div>

          <!-- 提示文字 -->
          <div class="mt-3 text-center">
            <p v-if="isLoggedIn" class="text-[11px] text-gray-400">
              按 <kbd class="px-1.5 py-0.5 bg-gray-100 rounded text-gray-600 font-mono">Enter</kbd> 发送，<kbd class="px-1.5 py-0.5 bg-gray-100 rounded text-gray-600 font-mono">Shift + Enter</kbd> 换行
            </p>
            <p v-else class="text-[11px] text-gray-500">
              <span class="text-blue-600 cursor-pointer hover:text-blue-700 font-medium" @click="openAuthDialog(true)">登录</span> 或 
              <span class="text-blue-600 cursor-pointer hover:text-blue-700 font-medium" @click="openAuthDialog(false)">注册</span> 后即可使用
            </p>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, reactive, computed } from 'vue'
import AuthDialog from './components/AuthDialog.vue'

const API_BASE_URL = '/api/v1'
const sessionId = ref(localStorage.getItem('chat_session_id'))
const isProcessing = ref(false)
const selectedImages = ref([])
const userInput = ref('')
const messages = ref([])
const chatContainer = ref(null)
const imageInput = ref(null)
const fileInput = ref(null)
const textareaRef = ref(null)
const isRecording = ref(false)
let abortController = null
let mediaRecorder = null
let audioChunks = []

// 登录状态管理
const isLoggedIn = ref(localStorage.getItem('isLoggedIn') === 'true')
const user = ref(JSON.parse(localStorage.getItem('user') || '{}'))
const authDialogVisible = ref(false)
const authDialogIsLogin = ref(true)

// 历史记录管理
const historyDialogVisible = ref(false)
const sessions = ref([])
const isLoadingHistory = ref(false)

// 清空对话
const clearChat = () => {
  if (messages.value.length > 0 && confirm('确定要清空所有对话吗？')) {
    messages.value = []
    localStorage.removeItem('chat_session_id')
    sessionId.value = null
  }
}

// 切换历史记录对话框
const toggleHistory = async () => {
  if (!isLoggedIn.value) {
    openAuthDialog(true)
    return
  }
  historyDialogVisible.value = true
  await loadSessions()
}

// 加载会话列表
const loadSessions = async () => {
  try {
    isLoadingHistory.value = true
    let userId = 'anonymous'
    if (isLoggedIn.value) {
      if (user.value && user.value.id) {
        userId = user.value.id.toString()
      } else {
        console.error('User ID not found in user object:', user.value)
      }
    }
    console.log('Loading sessions for user:', userId)
    console.log('User object:', user.value)
    console.log('Is logged in:', isLoggedIn.value)
    const response = await fetch(`${API_BASE_URL}/chat/user/${userId}/sessions`)
    console.log('Response status:', response.status)
    if (response.ok) {
      const data = await response.json()
      console.log('Sessions response:', data)
      if (data.success) {
        sessions.value = data.data.sessions
        console.log('Loaded sessions:', sessions.value)
      }
    } else {
      console.error('Failed to load sessions:', response.status, response.statusText)
    }
  } catch (error) {
    console.error('加载会话失败:', error)
  } finally {
    isLoadingHistory.value = false
  }
}

// 加载会话详情
const loadSession = async (sessionIdValue) => {
  try {
    isProcessing.value = true
    sessionId.value = sessionIdValue
    localStorage.setItem('chat_session_id', sessionIdValue)
    
    // 清空当前消息
    messages.value = []
    
    // 加载会话消息
    const response = await fetch(`${API_BASE_URL}/chat/session/${sessionIdValue}/messages`)
    if (response.ok) {
      const data = await response.json()
      if (data.success) {
        // 转换消息格式
        const sessionMessages = data.data.messages.map(msg => ({
          role: msg.role,
          content: msg.content,
          agentType: msg.agent_type,
          imageCount: msg.metadata?.image_count || 0
        }))
        messages.value = sessionMessages
      }
    }
    
    historyDialogVisible.value = false
  } catch (error) {
    console.error('加载会话详情失败:', error)
  } finally {
    isProcessing.value = false
  }
}

// 格式化时间
const formatTime = (timestamp) => {
  const date = new Date(parseInt(timestamp))
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 处理输入框点击
const handleInputClick = () => {
  if (!isLoggedIn.value) {
    openAuthDialog(true)
  }
}



// 获取Agent显示标签
const getAgentLabel = (type) => {
  const labels = {
    'general': '通用助手',
    'database': '数据库助手',
    'mcp': '工具助手',
    'vision': '视觉助手'
  }
  return labels[type] || type
}

// 自动调整文本框高度
const autoResize = () => {
  if (textareaRef.value) {
    textareaRef.value.style.height = 'auto'
    textareaRef.value.style.height = Math.min(textareaRef.value.scrollHeight, 200) + 'px'
  }
}

// 监听消息变化，自动滚动到底部
watch(messages, () => {
  scrollToBottom()
}, { deep: true })

const scrollToBottom = () => {
  if (chatContainer.value) {
    setTimeout(() => {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }, 100)
  }
}

const triggerImageUpload = () => {
  if (imageInput.value) {
    imageInput.value.click()
  }
}

const removeImage = (index) => {
  selectedImages.value.splice(index, 1)
}

const handleImageUpload = (event) => {
  const files = Array.from(event.target.files)
  if (!files.length) return

  const remaining = 5 - selectedImages.value.length
  if (remaining <= 0) {
    alert('最多上传5张图片')
    event.target.value = ''
    return
  }

  const toProcess = files.slice(0, remaining)
  let processed = 0

  toProcess.forEach(file => {
    const reader = new FileReader()
    reader.onload = function(e) {
      const img = new Image()
      img.onload = function() {
        const maxDimension = 2048
        let width = img.width
        let height = img.height

        if (width > maxDimension || height > maxDimension) {
          const ratio = Math.min(maxDimension / width, maxDimension / height)
          width *= ratio
          height *= ratio
        }

        const canvas = document.createElement('canvas')
        canvas.width = width
        canvas.height = height
        const ctx = canvas.getContext('2d')
        ctx.drawImage(img, 0, 0, width, height)

        const base64Data = canvas.toDataURL('image/jpeg', 0.8)
        selectedImages.value.push(base64Data)
        processed++
      }
      img.src = e.target.result
    }
    reader.readAsDataURL(file)
  })

  event.target.value = ''
}

const triggerFileUpload = () => {
  if (fileInput.value) {
    fileInput.value.click()
  }
}

const handleFileUpload = (event) => {
  const file = event.target.files[0]
  if (!file) return

  // 这里可以添加文件处理逻辑
  alert(`文件 ${file.name} 已选择，大小：${(file.size / 1024).toFixed(2)}KB`)
  event.target.value = ''
}

const toggleVoiceRecording = async () => {
  if (isRecording.value) {
    // 停止录音
    if (mediaRecorder) {
      mediaRecorder.stop()
    }
    isRecording.value = false
  } else {
    // 开始录音
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      mediaRecorder = new MediaRecorder(stream)
      audioChunks = []

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunks.push(event.data)
        }
      }

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' })
        // 这里可以添加语音处理逻辑
        alert('录音已完成')
        // 关闭媒体流
        stream.getTracks().forEach(track => track.stop())
      }

      mediaRecorder.start()
      isRecording.value = true
    } catch (error) {
      console.error('录音失败:', error)
      alert('无法访问麦克风，请检查权限')
    }
  }
}

const sendMessage = async () => {
  if (!isLoggedIn.value) {
    openAuthDialog(true)
    return
  }
  
  let message = userInput.value.trim()
  if (!message && selectedImages.value.length === 0) return
  if (isProcessing.value) return

  isProcessing.value = true

  messages.value.push({
    role: 'user',
    content: message || '分析图片',
    imageCount: selectedImages.value.length
  })
  
  userInput.value = ''

  const assistantMessage = reactive({
    role: 'assistant',
    content: '',
    agentType: 'general'
  })
  messages.value.push(assistantMessage)

  try {
    abortController = new AbortController()

    // 确保user_id正确获取
    let userId = 'anonymous'
    if (isLoggedIn.value) {
      if (user.value && user.value.id) {
        userId = user.value.id.toString()
      } else {
        console.error('User ID not found in user object:', user.value)
      }
    }
    const payload = {
      message: message || '分析图片',
      session_id: sessionId.value || null,
      user_id: userId,
      images: selectedImages.value
    }
    console.log('Sending message with payload:', payload)
    console.log('User ID being used:', userId)

    console.log('Sending SSE request:', payload)

    const response = await fetch(`${API_BASE_URL}/agent/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream'
      },
      body: JSON.stringify(payload),
      signal: abortController.signal
    })

    console.log('SSE Response:', response)
    console.log('Status:', response.status)
    console.log('Headers:', Object.fromEntries(response.headers.entries()))

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      console.log('Received chunk:', value)
      
      buffer += decoder.decode(value, { stream: true })
      console.log('Buffer:', buffer)
      
      const lines = buffer.split('\n')
      console.log('Lines:', lines)
      
      buffer = lines.pop() || ''

      for (const line of lines) {
        const trimmedLine = line.trim()
        console.log('Processing line:', trimmedLine)
        
        if (trimmedLine.startsWith('data: ')) {
          try {
            const jsonStr = trimmedLine.slice(6)
            if (!jsonStr) continue
            
            console.log('JSON string:', jsonStr)
            const data = JSON.parse(jsonStr)
            console.log('Parsed data:', data)
            
            if (data.type === 'session') {
              sessionId.value = data.session_id
              localStorage.setItem('chat_session_id', sessionId.value)
              console.log('Session ID:', data.session_id)
            } else if (data.type === 'metadata') {
              assistantMessage.agentType = data.agent_type
              console.log('Agent type:', data.agent_type)
            } else if (data.type === 'content') {
              assistantMessage.content += data.content
              console.log('Content chunk:', data.content)
              console.log('Full content:', assistantMessage.content)
            } else if (data.type === 'error') {
              assistantMessage.content = `错误: ${data.content}`
              console.log('Error:', data.content)
            } else if (data.type === 'done') {
              console.log('Stream done')
              break
            }
          } catch (e) {
            console.error('Failed to parse SSE data:', e, trimmedLine)
          }
        }
      }
    }
  } catch (error) {
    console.error('Stream error:', error)
    if (error.name === 'AbortError') {
      assistantMessage.content = '请求超时，请稍后重试'
    } else {
      assistantMessage.content = `网络错误: ${error.message}`
    }
  } finally {
    abortController = null
    isProcessing.value = false
    selectedImages.value = []
  }
}

// 打开登录/注册对话框
const openAuthDialog = (isLogin) => {
  authDialogIsLogin.value = isLogin
  authDialogVisible.value = true
}

// 关闭登录/注册对话框
const closeAuthDialog = () => {
  authDialogVisible.value = false
}

// 处理登录成功
const handleLoginSuccess = (userData) => {
  isLoggedIn.value = true
  user.value = userData
  localStorage.setItem('isLoggedIn', 'true')
  localStorage.setItem('user', JSON.stringify(userData))
  console.log('Login success, user data:', userData)
  console.log('User ID:', userData.id)
}

// 处理按钮点击
const handleButtonClick = (callback) => {
  if (!isLoggedIn.value) {
    openAuthDialog(true)
    return
  }
  callback()
}

// 退出登录
const logout = () => {
  if (confirm('确定要退出登录吗？')) {
    localStorage.removeItem('isLoggedIn')
    localStorage.removeItem('user')
    isLoggedIn.value = false
    user.value = {}
  }
}

onMounted(() => {
  // 初始化时聚焦输入框
  if (textareaRef.value) {
    textareaRef.value.focus()
  }
  
  // 页面加载时，检查是否存在session_id
  if (sessionId.value) {
    loadSession(sessionId.value)
  }
})
</script>