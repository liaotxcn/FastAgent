<template>
  <div class="flex flex-col h-screen bg-gradient-to-br from-gray-50 to-gray-100 relative overflow-hidden">
    <!-- 背景图片 -->
    <div class="absolute top-0 left-0 w-1/3 h-full opacity-10 pointer-events-none">
      <img src="/src/hello.png" alt="Background" class="absolute top-20 left-10 w-40 h-40 object-contain" />
      <img src="/src/run.png" alt="Background" class="absolute bottom-20 left-10 w-40 h-40 object-contain" />
    </div>
    <div class="absolute top-0 right-0 w-1/3 h-full opacity-10 pointer-events-none">
      <img src="/src/sleep.png" alt="Background" class="absolute top-20 right-10 w-40 h-40 object-contain" />
      <img src="/src/logo.png" alt="Background" class="absolute bottom-20 right-10 w-40 h-40 object-contain" />
    </div>
    <!-- 顶部导航 -->
    <header class="bg-white/80 backdrop-blur-md border-b border-gray-200/50 px-6 py-4 sticky top-0 z-10">
      <div class="max-w-4xl mx-auto flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl flex items-center justify-center overflow-hidden shadow-lg shadow-blue-500/20">
            <img src="/src/logo.png" alt="FastAgent" class="w-full h-full object-contain" />
          </div>
          <div>
            <h1 class="text-xl font-bold bg-gradient-to-r from-gray-800 to-gray-600 bg-clip-text text-transparent">FastAgent</h1>
            <p class="text-xs text-gray-500">智能助手</p>
          </div>
        </div>
        <div class="flex items-center gap-3">
          <!-- 历史记录按钮 -->
          <button 
            @click="toggleHistory" 
            class="text-gray-400 hover:text-blue-500 transition-colors p-2 rounded-lg hover:bg-blue-50"
            title="历史对话"
          >
            <i class="fa fa-history"></i>
          </button>
          <!-- 清空对话按钮 -->
          <button 
            @click="clearChat" 
            class="text-gray-400 hover:text-red-500 transition-colors p-2 rounded-lg hover:bg-red-50"
            title="清空对话"
          >
            <i class="fa fa-trash-o"></i>
          </button>
          <!-- 登录状态 -->
          <div v-if="isLoggedIn" class="flex items-center gap-2">
            <div class="w-8 h-8 bg-gradient-to-br from-blue-400 to-blue-600 rounded-full flex items-center justify-center text-white font-medium text-sm">
              {{ user.username.charAt(0).toUpperCase() }}
            </div>
            <span class="text-sm font-medium text-gray-700">{{ user.username }}</span>
            <button 
              @click="logout" 
              class="text-gray-400 hover:text-red-500 transition-colors p-2 rounded-lg hover:bg-red-50"
              title="退出登录"
            >
              <i class="fa fa-sign-out"></i>
            </button>
          </div>
          <!-- 未登录状态 -->
          <div v-else class="flex items-center gap-2">
            <button 
              @click="openAuthDialog(true)" 
              class="px-3 py-1.5 text-sm bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              登录
            </button>
            <button 
              @click="openAuthDialog(false)" 
              class="px-3 py-1.5 text-sm bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-lg hover:from-blue-600 hover:to-blue-700 transition-colors"
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
    <div v-if="historyDialogVisible" class="fixed inset-y-0 left-0 bg-white shadow-2xl z-50 w-[320px] max-w-[80vw] flex flex-col transform transition-transform duration-300 ease-in-out">
      <div class="flex items-center justify-between p-6 border-b border-gray-200">
        <h2 class="text-xl font-bold text-gray-800">历史对话</h2>
        <button 
          @click="historyDialogVisible = false" 
          class="text-gray-400 hover:text-gray-600 transition-colors p-2 rounded-lg hover:bg-gray-100"
        >
          <i class="fa fa-times"></i>
        </button>
      </div>
      <div class="flex-1 overflow-y-auto p-4">
        <div v-if="isLoadingHistory" class="flex items-center justify-center h-32">
          <div class="loading-dots">
            <span></span><span></span><span></span>
          </div>
        </div>
        <div v-else-if="sessions.length === 0" class="flex flex-col items-center justify-center h-32 text-gray-400">
          <i class="fa fa-comments-o text-4xl mb-2"></i>
          <p>暂无历史对话</p>
        </div>
        <div v-else class="space-y-3">
          <div 
            v-for="session in sessions" 
            :key="session.session_id"
            class="bg-gray-50 rounded-xl p-4 hover:bg-gray-100 transition-colors cursor-pointer"
            @click="loadSession(session.session_id)"
          >
            <div class="flex items-center justify-between">
              <h3 class="font-medium text-gray-800 truncate">{{ session.title || '未命名对话' }}</h3>
              <span class="text-xs text-gray-500">{{ formatTime(session.updated_at) }}</span>
            </div>
            <p class="text-sm text-gray-500 mt-1 truncate">{{ session.message_count }} 条消息</p>
          </div>
        </div>
      </div>
      <div class="p-4 border-t border-gray-200 flex justify-end">
        <button 
          @click="historyDialogVisible = false" 
          class="px-4 py-2 text-sm bg-gray-200 hover:bg-gray-300 text-gray-800 rounded-lg transition-colors"
        >
          关闭
        </button>
      </div>
    </div>
    <!-- 背景遮罩 -->
    <div v-if="historyDialogVisible" class="fixed inset-0 bg-black/20 backdrop-blur-sm z-40" @click="historyDialogVisible = false"></div>


    <!-- 主内容区 -->
    <main class="flex-1 overflow-hidden flex flex-col max-w-4xl mx-auto w-full">
      <!-- 聊天区域 -->
      <div 
        ref="chatContainer" 
        class="flex-1 overflow-y-auto p-4 space-y-6 scroll-smooth"
      >
        <!-- 空状态 -->
        <div v-if="messages.length === 0" class="flex flex-col items-center justify-center h-full text-gray-400 space-y-4">
          <div class="w-20 h-20 bg-gradient-to-br from-blue-100 to-purple-100 rounded-2xl flex items-center justify-center">
            <i class="fa fa-comments text-3xl text-blue-500"></i>
          </div>
          <p v-if="isLoggedIn" class="text-sm">开始一段新的对话吧...</p>
          <div v-else class="text-center space-y-2">
            <p class="text-sm text-gray-500">请先登录后使用对话功能</p>
            <button 
              @click="openAuthDialog(true)" 
              class="px-4 py-2 text-sm bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-lg hover:from-blue-600 hover:to-blue-700 transition-colors"
            >
              立即登录
            </button>
          </div>
          <div class="space-y-2">
            <div class="flex gap-2 text-xs">
              <span class="px-3 py-1 bg-white rounded-full shadow-sm text-gray-500">💬 智能问答</span>
              <span class="px-3 py-1 bg-white rounded-full shadow-sm text-gray-500">🖼️ 图片分析</span>
              <span class="px-3 py-1 bg-white rounded-full shadow-sm text-gray-500">🗄️ 数据查询</span>
            </div>
            <div class="flex gap-2 text-xs">
              <span class="px-3 py-1 bg-white rounded-full shadow-sm text-gray-500">🔍 信息检索</span>
              <span class="px-3 py-1 bg-white rounded-full shadow-sm text-gray-500">📍 位置导航</span>
              <span class="px-3 py-1 bg-white rounded-full shadow-sm text-gray-500">📋 事务处理</span>
            </div>
          </div>
        </div>

        <!-- 消息列表 -->
        <transition-group name="message">
          <div 
            v-for="(message, index) in messages" 
            :key="index"
            class="message flex animate-fade-in" 
            :class="message.role === 'user' ? 'justify-end' : 'justify-start'"
          >
            <!-- AI头像 -->
            <div v-if="message.role === 'assistant'" class="mr-3 flex-shrink-0">
              <div class="w-8 h-8 rounded-full flex items-center justify-center overflow-hidden shadow-md">
                <img src="/src/logo.png" alt="AI" class="w-full h-full object-contain" />
              </div>
            </div>

            <!-- 消息气泡 -->
            <div 
              class="max-w-[75%] rounded-2xl px-5 py-3.5 shadow-sm" 
              :class="message.role === 'user' 
                ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-br-md shadow-blue-500/20' 
                : 'bg-white text-gray-800 rounded-bl-md shadow-gray-200/50 border border-gray-100'"
            >
              <!-- Agent类型标签 -->
              <div v-if="message.role === 'assistant' && message.agentType" class="flex items-center gap-1.5 mb-2">
                <span class="text-[10px] px-2 py-0.5 bg-blue-50 text-blue-600 rounded-full font-medium">
                  {{ getAgentLabel(message.agentType) }}
                </span>
              </div>

              <!-- 图片标记 -->
              <div v-if="message.role === 'user' && message.imageCount > 0" class="flex items-center gap-1.5 mb-2 text-blue-100">
                <i class="fa fa-image text-xs"></i>
                <span class="text-xs">{{ message.imageCount }}张图片</span>
              </div>

              <!-- 消息内容 -->
              <div class="whitespace-pre-wrap text-[15px] leading-relaxed">{{ message.content }}</div>
            </div>

            <!-- 用户头像 -->
            <div v-if="message.role === 'user'" class="ml-3 flex-shrink-0">
              <div class="w-8 h-8 bg-gradient-to-br from-gray-400 to-gray-500 rounded-full flex items-center justify-center shadow-md">
                <i class="fa fa-user text-white text-xs"></i>
              </div>
            </div>
          </div>
        </transition-group>

        <!-- 加载状态 -->
        <div v-if="isProcessing" class="message flex justify-start animate-fade-in">
          <div class="mr-3 flex-shrink-0">
            <div class="w-8 h-8 rounded-full flex items-center justify-center overflow-hidden shadow-md">
              <img src="/src/logo.png" alt="AI" class="w-full h-full object-contain" />
            </div>
          </div>
          <div class="bg-white rounded-2xl rounded-bl-md shadow-sm border border-gray-100 px-5 py-4">
            <div class="loading-dots">
              <span></span><span></span><span></span>
            </div>
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="bg-white/80 backdrop-blur-md border-t border-gray-200/50 p-4">
        <div class="max-w-4xl mx-auto">
          <!-- 图片预览 -->
          <div v-if="selectedImages.length > 0" class="flex gap-2 mb-3 flex-wrap">
            <div 
              v-for="(src, index) in selectedImages" 
              :key="index"
              class="relative group"
            >
              <img 
                :src="src" 
                class="w-14 h-14 object-cover rounded-lg border border-gray-200 group-hover:border-blue-400 transition-colors"
              />
              <button 
                @click="removeImage(index)"
                class="absolute -top-1.5 -right-1.5 w-5 h-5 bg-red-500 text-white rounded-full text-xs flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity shadow-md hover:bg-red-600"
              >
                <i class="fa fa-times text-[10px]"></i>
              </button>
            </div>
          </div>

          <!-- 输入框 -->
          <div class="flex gap-3 items-end">
            <button 
              @click="handleButtonClick(triggerImageUpload)"
              :disabled="!isLoggedIn"
              class="p-3 text-gray-400 hover:text-blue-500 hover:bg-blue-50 rounded-xl transition-all duration-200 flex-shrink-0 disabled:opacity-50 disabled:cursor-not-allowed"
              :class="{ 'text-blue-500 bg-blue-50': selectedImages.length > 0 }"
              title="上传图片"
            >
              <i class="fa fa-image text-lg"></i>
              <span v-if="selectedImages.length > 0" class="ml-1 text-xs font-medium">{{ selectedImages.length }}</span>
              <input 
                ref="imageInput" 
                type="file" 
                accept="image/*" 
                multiple 
                class="hidden" 
                @change="handleImageUpload"
              />
            </button>

            <button 
              @click="handleButtonClick(triggerFileUpload)"
              :disabled="!isLoggedIn"
              class="p-3 text-gray-400 hover:text-blue-500 hover:bg-blue-50 rounded-xl transition-all duration-200 flex-shrink-0 disabled:opacity-50 disabled:cursor-not-allowed"
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

            <button 
              @click="handleButtonClick(toggleVoiceRecording)"
              :disabled="!isLoggedIn"
              class="p-3 text-gray-400 hover:text-blue-500 hover:bg-blue-50 rounded-xl transition-all duration-200 flex-shrink-0 disabled:opacity-50 disabled:cursor-not-allowed"
              :class="{ 'text-red-500 bg-red-50': isRecording }"
              title="语音输入"
            >
              <i class="fa fa-microphone text-lg"></i>
            </button>

            <div class="flex-1 relative">
              <textarea 
                v-model="userInput" 
                rows="1" 
                :disabled="!isLoggedIn"
                class="w-full bg-gray-100/50 border-0 rounded-2xl px-4 py-3.5 pr-12 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:bg-white transition-all resize-none text-[15px] disabled:bg-gray-200/50 disabled:cursor-not-allowed"
                :placeholder="isLoggedIn ? '输入您的问题，按 Enter 发送...' : '请先登录后使用对话功能'"
                @keydown.enter.prevent="sendMessage"
                @input="autoResize"
                @click="handleInputClick"
                ref="textareaRef"
              ></textarea>
            </div>

            <button 
              @click="sendMessage"
              :disabled="!isLoggedIn || isProcessing || (!userInput.trim() && selectedImages.length === 0)"
              class="p-3.5 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 disabled:from-gray-300 disabled:to-gray-300 text-white rounded-xl transition-all duration-200 shadow-lg shadow-blue-500/25 disabled:shadow-none flex-shrink-0"
            >
              <i v-if="!isProcessing" class="fa fa-paper-plane"></i>
              <i v-else class="fa fa-spinner fa-spin"></i>
            </button>
          </div>

          <!-- 提示文字 -->
          <div class="mt-2 text-center">
            <p v-if="isLoggedIn" class="text-[11px] text-gray-400">按 Enter 发送，Shift + Enter 换行</p>
            <p v-else class="text-[11px] text-gray-500">
              <span class="text-blue-500 cursor-pointer hover:text-blue-600" @click="openAuthDialog(true)">登录</span> 或 
              <span class="text-blue-500 cursor-pointer hover:text-blue-600" @click="openAuthDialog(false)">注册</span> 后即可使用对话功能
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

<style scoped>
/* 消息进入动画 */
.message-enter-active,
.message-leave-active {
  transition: all 0.3s ease;
}

.message-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.message-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* 淡入动画 */
.animate-fade-in {
  animation: fadeIn 0.3s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 加载动画 */
.loading-dots {
  display: flex;
  gap: 4px;
  align-items: center;
  height: 20px;
}

.loading-dots span {
  width: 6px;
  height: 6px;
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  border-radius: 50%;
  animation: loading 1.4s infinite ease-in-out both;
}

.loading-dots span:nth-child(1) {
  animation-delay: -0.32s;
}

.loading-dots span:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes loading {
  0%, 80%, 100% {
    transform: scale(0.6);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

/* 滚动条样式 */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

/* 选中文字样式 */
::selection {
  background: rgba(59, 130, 246, 0.2);
  color: inherit;
}
</style>