<template>
  <div class="flex flex-col h-screen bg-gradient-to-br from-gray-50 to-gray-100">
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
        <button 
          @click="clearChat" 
          class="text-gray-400 hover:text-red-500 transition-colors p-2 rounded-lg hover:bg-red-50"
          title="清空对话"
        >
          <i class="fa fa-trash-o"></i>
        </button>
      </div>
    </header>

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
          <p class="text-sm">开始一段新的对话吧...</p>
          <div class="flex gap-2 text-xs">
            <span class="px-3 py-1 bg-white rounded-full shadow-sm text-gray-500">💬 智能问答</span>
            <span class="px-3 py-1 bg-white rounded-full shadow-sm text-gray-500">🖼️ 图片分析</span>
            <span class="px-3 py-1 bg-white rounded-full shadow-sm text-gray-500">🗄️ 数据查询</span>
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
              @click="triggerImageUpload"
              class="p-3 text-gray-400 hover:text-blue-500 hover:bg-blue-50 rounded-xl transition-all duration-200 flex-shrink-0"
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

            <div class="flex-1 relative">
              <textarea 
                v-model="userInput" 
                rows="1" 
                class="w-full bg-gray-100/50 border-0 rounded-2xl px-4 py-3.5 pr-12 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:bg-white transition-all resize-none text-[15px]"
                placeholder="输入您的问题，按 Enter 发送..."
                @keydown.enter.prevent="sendMessage"
                @input="autoResize"
                ref="textareaRef"
              ></textarea>
            </div>

            <button 
              @click="sendMessage"
              :disabled="isProcessing || (!userInput.trim() && selectedImages.length === 0)"
              class="p-3.5 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 disabled:from-gray-300 disabled:to-gray-300 text-white rounded-xl transition-all duration-200 shadow-lg shadow-blue-500/25 disabled:shadow-none flex-shrink-0"
            >
              <i v-if="!isProcessing" class="fa fa-paper-plane"></i>
              <i v-else class="fa fa-spinner fa-spin"></i>
            </button>
          </div>

          <!-- 提示文字 -->
          <div class="mt-2 text-center">
            <p class="text-[11px] text-gray-400">按 Enter 发送，Shift + Enter 换行</p>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'

const API_BASE_URL = '/api/v1'
const sessionId = ref(localStorage.getItem('chat_session_id'))
const isProcessing = ref(false)
const selectedImages = ref([])
const userInput = ref('')
const messages = ref([])
const chatContainer = ref(null)
const imageInput = ref(null)
const textareaRef = ref(null)
let abortController = null

// 清空对话
const clearChat = () => {
  if (messages.value.length > 0 && confirm('确定要清空所有对话吗？')) {
    messages.value = []
    localStorage.removeItem('chat_session_id')
    sessionId.value = null
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

const sendMessage = async () => {
  let message = userInput.value.trim()
  if (!message && selectedImages.value.length === 0) return
  if (isProcessing.value) return

  // 数据库查询预处理：确保是SELECT语句
  if (message.toLowerCase().includes('查询') && (message.toLowerCase().includes('表') || message.toLowerCase().includes('from'))) {
    if (!message.toLowerCase().startsWith('select')) {
      // 简单直接的处理：统一转换为SELECT * FROM table
      // 提取表名
      let tableName = ''
      const tableMatch = message.match(/(表|from)\s*([\w_]+)/i)
      if (tableMatch) {
        tableName = tableMatch[2]
      } else {
        // 尝试从查询内容中提取表名
        const contentMatch = message.match(/查询.*?(\w+)/i)
        if (contentMatch) {
          tableName = contentMatch[1]
        }
      }
      
      if (tableName) {
        message = `SELECT * FROM ${tableName}`
      }
    }
  }

  isProcessing.value = true

  // 添加用户消息
  messages.value.push({
    role: 'user',
    content: message || '分析图片',
    imageCount: selectedImages.value.length
  })
  
  userInput.value = ''

  try {
    abortController = new AbortController()
    // 设置3分钟超时
    const timeoutId = setTimeout(() => abortController.abort(), 180000)

    const payload = {
      message: message || '分析图片',
      session_id: sessionId.value || null,
      images: selectedImages.value
    }

    const response = await fetch(`${API_BASE_URL}/agent/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload),
      signal: abortController.signal
    })

    clearTimeout(timeoutId)

    const result = await response.json()

    if (result.success && result.data) {
      if (result.data.session_id) {
        sessionId.value = result.data.session_id
        localStorage.setItem('chat_session_id', sessionId.value)
      }
      
      const output = result.data.output || '抱歉，没有收到响应。'
      const agentType = result.data.agent_type || 'general'
      messages.value.push({
        role: 'assistant',
        content: output,
        agentType: agentType
      })
    } else {
      messages.value.push({
        role: 'assistant',
        content: `错误: ${result.message || result.error || '请求失败'}`
      })
    }
  } catch (error) {
    if (error.name === 'AbortError') {
      messages.value.push({
        role: 'assistant',
        content: '请求超时，请稍后重试'
      })
    } else {
      messages.value.push({
        role: 'assistant',
        content: `网络错误: ${error.message}`
      })
    }
  } finally {
    abortController = null
    isProcessing.value = false
    
    // 清空图片选择
    selectedImages.value = []
  }
}

onMounted(() => {
  // 初始化时聚焦输入框
  if (textareaRef.value) {
    textareaRef.value.focus()
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