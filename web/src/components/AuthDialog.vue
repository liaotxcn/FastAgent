<template>
  <div v-if="isVisible" class="fixed inset-0 bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 z-50 flex items-center justify-center p-4 overflow-y-auto">
    <div class="bg-white rounded-3xl shadow-2xl w-full max-w-5xl overflow-hidden my-8 transform transition-all duration-300 scale-95 animate-scale-in">
      <div class="flex flex-col md:flex-row">
        <!-- 左侧：表单区域 -->
        <div class="w-full md:w-1/2 p-8 md:p-12 flex flex-col">
          <!-- 关闭按钮 -->
          <div class="flex justify-end mb-6">
            <button 
              @click="$emit('close')" 
              class="text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-all duration-200 p-2 rounded-xl"
            >
              <i class="fa fa-times text-xl"></i>
            </button>
          </div>
          
          <!-- 标题 -->
          <div class="mb-8">
            <h1 class="text-3xl font-bold bg-gradient-to-r from-gray-800 to-gray-600 bg-clip-text text-transparent mb-2">FastAgent</h1>
            <p class="text-gray-500">{{ isLogin ? '欢迎回来' : '创建账户' }}</p>
          </div>
          
          <!-- 切换标签 -->
          <div class="flex mb-8 bg-gray-100 p-1 rounded-xl">
            <button 
              @click="isLogin = true" 
              class="flex-1 px-4 py-2.5 text-sm font-medium rounded-lg transition-all duration-200" 
              :class="isLogin ? 'bg-white text-gray-800 shadow-sm' : 'text-gray-500 hover:text-gray-700'"
            >
              登录
            </button>
            <button 
              @click="isLogin = false" 
              class="flex-1 px-4 py-2.5 text-sm font-medium rounded-lg transition-all duration-200" 
              :class="!isLogin ? 'bg-white text-gray-800 shadow-sm' : 'text-gray-500 hover:text-gray-700'"
            >
              注册
            </button>
          </div>
          
          <!-- 登录表单 -->
          <div v-show="isLogin" class="space-y-5 flex-grow">
            <!-- 用户名 -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">用户名</label>
              <input 
                v-model="form.username" 
                type="text" 
                class="w-full px-4 py-3.5 bg-gray-50 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 focus:bg-white outline-none transition-all duration-200"
                placeholder="请输入用户名"
                @input="clearError"
              />
              <div v-if="errors.username" class="text-red-500 text-xs mt-1.5">{{ errors.username }}</div>
            </div>
            
            <!-- 密码 -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">密码</label>
              <div class="relative">
                <input 
                  v-model="form.password" 
                  :type="showPassword ? 'text' : 'password'" 
                  class="w-full px-4 py-3.5 pr-12 bg-gray-50 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 focus:bg-white outline-none transition-all duration-200"
                  placeholder="请输入密码"
                  @input="clearError"
                />
                <button 
                  @click="showPassword = !showPassword" 
                  class="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <i :class="showPassword ? 'fa fa-eye-slash' : 'fa fa-eye'"></i>
                </button>
              </div>
              <div v-if="errors.password" class="text-red-500 text-xs mt-1.5">{{ errors.password }}</div>
            </div>
            
            <!-- 邮箱 -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">邮箱</label>
              <div class="flex gap-3">
                <input 
                  v-model="form.email" 
                  type="email" 
                  class="flex-1 px-4 py-3.5 bg-gray-50 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 focus:bg-white outline-none transition-all duration-200"
                  placeholder="请输入邮箱"
                  @input="clearError"
                />
                <button 
                  @click="sendCode" 
                  :disabled="isSendingCode" 
                  class="px-5 py-3.5 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl hover:from-blue-700 hover:to-indigo-700 disabled:from-gray-300 disabled:to-gray-300 disabled:cursor-not-allowed transition-all duration-200 whitespace-nowrap font-medium shadow-lg shadow-blue-500/20"
                >
                  {{ isSendingCode ? '发送中...' : codeCountdown > 0 ? `${codeCountdown}s` : '获取验证码' }}
                </button>
              </div>
              <div v-if="errors.email" class="text-red-500 text-xs mt-1.5">{{ errors.email }}</div>
            </div>
            
            <!-- 邮箱验证码 -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">验证码</label>
              <input 
                v-model="form.emailCode" 
                type="text" 
                class="w-full px-4 py-3.5 bg-gray-50 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 focus:bg-white outline-none transition-all duration-200"
                placeholder="请输入6位验证码"
                maxlength="6"
                @input="clearError"
              />
              <div v-if="errors.emailCode" class="text-red-500 text-xs mt-1.5">{{ errors.emailCode }}</div>
            </div>
            
            <!-- 错误/成功信息 -->
            <div v-if="error" :class="error === '注册成功，请登录' ? 'text-green-600 text-sm p-4 bg-green-50 rounded-xl animate-slide-down' : 'text-red-500 text-sm p-4 bg-red-50 rounded-xl animate-slide-down'">
              <i :class="error === '注册成功，请登录' ? 'fa fa-check-circle mr-2' : 'fa fa-exclamation-circle mr-2'"></i>
              {{ error }}
            </div>
            
            <!-- 提交按钮 -->
            <button 
              @click="submit" 
              :disabled="isSubmitting" 
              class="w-full py-4 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 disabled:from-gray-300 disabled:to-gray-300 text-white rounded-xl font-medium transition-all duration-300 shadow-xl shadow-blue-500/30 disabled:shadow-none mt-6"
            >
              {{ isSubmitting ? '处理中...' : (isLogin ? '登录' : '注册') }}
            </button>
          </div>
          
          <!-- 注册表单 -->
          <div v-show="!isLogin" class="space-y-5 flex-grow">
            <!-- 用户名 -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">用户名</label>
              <input 
                v-model="form.username" 
                type="text" 
                class="w-full px-4 py-3.5 bg-gray-50 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 focus:bg-white outline-none transition-all duration-200"
                placeholder="请输入用户名"
                @input="clearError"
              />
              <div v-if="errors.username" class="text-red-500 text-xs mt-1.5">{{ errors.username }}</div>
            </div>
            
            <!-- 密码 -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">密码</label>
              <div class="relative">
                <input 
                  v-model="form.password" 
                  :type="showPassword ? 'text' : 'password'" 
                  class="w-full px-4 py-3.5 pr-12 bg-gray-50 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 focus:bg-white outline-none transition-all duration-200"
                  placeholder="请输入密码（至少6位）"
                  @input="clearError"
                />
                <button 
                  @click="showPassword = !showPassword" 
                  class="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <i :class="showPassword ? 'fa fa-eye-slash' : 'fa fa-eye'"></i>
                </button>
              </div>
              <div v-if="errors.password" class="text-red-500 text-xs mt-1.5">{{ errors.password }}</div>
            </div>
            
            <!-- 确认密码 -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">确认密码</label>
              <div class="relative">
                <input 
                  v-model="form.confirmPassword" 
                  :type="showPassword ? 'text' : 'password'" 
                  class="w-full px-4 py-3.5 pr-12 bg-gray-50 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 focus:bg-white outline-none transition-all duration-200"
                  placeholder="请再次输入密码"
                  @input="clearError"
                />
                <button 
                  @click="showPassword = !showPassword" 
                  class="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <i :class="showPassword ? 'fa fa-eye-slash' : 'fa fa-eye'"></i>
                </button>
              </div>
              <div v-if="errors.confirmPassword" class="text-red-500 text-xs mt-1.5">{{ errors.confirmPassword }}</div>
            </div>
            
            <!-- 邮箱 -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">邮箱</label>
              <input 
                v-model="form.email" 
                type="email" 
                class="w-full px-4 py-3.5 bg-gray-50 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 focus:bg-white outline-none transition-all duration-200"
                placeholder="请输入邮箱"
                @input="clearError"
              />
              <div v-if="errors.email" class="text-red-500 text-xs mt-1.5">{{ errors.email }}</div>
            </div>
            
            <!-- 错误信息 -->
            <div v-if="error" class="text-red-500 text-sm p-4 bg-red-50 rounded-xl animate-slide-down">
              <i class="fa fa-exclamation-circle mr-2"></i>
              {{ error }}
            </div>
            
            <!-- 提交按钮 -->
            <button 
              @click="submit" 
              :disabled="isSubmitting" 
              class="w-full py-4 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 disabled:from-gray-300 disabled:to-gray-300 text-white rounded-xl font-medium transition-all duration-300 shadow-xl shadow-blue-500/30 disabled:shadow-none mt-6"
            >
              {{ isSubmitting ? '处理中...' : '注册' }}
            </button>
          </div>
        </div>
        
        <!-- 右侧：图片区域 -->
        <div class="hidden md:flex w-1/2 bg-gradient-to-br from-blue-600 via-indigo-600 to-purple-700 p-12 flex-col justify-center relative overflow-hidden">
          <!-- 背景装饰 -->
          <div class="absolute inset-0">
            <div class="absolute top-1/4 left-1/4 w-64 h-64 bg-white/10 rounded-full blur-3xl"></div>
            <div class="absolute bottom-1/4 right-1/4 w-48 h-48 bg-white/10 rounded-full blur-2xl"></div>
          </div>
          
          <div class="relative text-white space-y-8">
            <div class="space-y-4">
              <h2 class="text-4xl font-bold leading-tight">Let's build a smarter world together</h2>
              <p class="text-blue-100 text-lg">Using FastAgent to create a better tomorrow</p>
            </div>
            
            <div class="flex justify-center">
              <div class="w-36 h-36 rounded-full bg-gradient-to-br from-white/20 to-white/5 flex items-center justify-center backdrop-blur-sm shadow-xl animate-float-logo">
                <img src="/src/resources/logo.png" alt="FastAgent" class="w-28 h-28 object-contain drop-shadow-2xl" />
              </div>
            </div>
            
            <div class="grid grid-cols-2 gap-6 mt-12">
              <div class="flex items-center gap-4 bg-white/10 backdrop-blur-sm rounded-2xl p-4">
                <div class="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
                  <i class="fa fa-comments text-white text-2xl"></i>
                </div>
                <span class="text-white font-medium">智能问答</span>
              </div>
              <div class="flex items-center gap-4 bg-white/10 backdrop-blur-sm rounded-2xl p-4">
                <div class="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
                  <i class="fa fa-search text-white text-2xl"></i>
                </div>
                <span class="text-white font-medium">信息检索</span>
              </div>
              <div class="flex items-center gap-4 bg-white/10 backdrop-blur-sm rounded-2xl p-4">
                <div class="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
                  <i class="fa fa-image text-white text-2xl"></i>
                </div>
                <span class="text-white font-medium">图片分析</span>
              </div>
              <div class="flex items-center gap-4 bg-white/10 backdrop-blur-sm rounded-2xl p-4">
                <div class="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
                  <i class="fa fa-map-marker text-white text-2xl"></i>
                </div>
                <span class="text-white font-medium">位置导航</span>
              </div>
              <div class="flex items-center gap-4 bg-white/10 backdrop-blur-sm rounded-2xl p-4">
                <div class="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
                  <i class="fa fa-database text-white text-2xl"></i>
                </div>
                <span class="text-white font-medium">数据查询</span>
              </div>
              <div class="flex items-center gap-4 bg-white/10 backdrop-blur-sm rounded-2xl p-4">
                <div class="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
                  <i class="fa fa-tasks text-white text-2xl"></i>
                </div>
                <span class="text-white font-medium">事务处理</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'

const props = defineProps({
  isVisible: {
    type: Boolean,
    default: false
  }
})

const isLogin = ref(true)

const emit = defineEmits(['close', 'login-success'])

const form = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  email: '',
  emailCode: ''
})

const isSubmitting = ref(false)
const isSendingCode = ref(false)
const codeCountdown = ref(0)
const error = ref('')
const showPassword = ref(false)
const errors = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  email: '',
  emailCode: ''
})

// 清除错误信息
const clearError = () => {
  error.value = ''
  Object.keys(errors).forEach(key => {
    errors[key] = ''
  })
}

// 验证表单
const validateForm = () => {
  let isValid = true
  clearError()
  
  if (!form.username.trim()) {
    errors.username = '请输入用户名'
    isValid = false
  }
  
  if (!form.password) {
    errors.password = '请输入密码'
    isValid = false
  }
  
  if (!form.email) {
    errors.email = '请输入邮箱'
    isValid = false
  } else if (!/^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$/.test(form.email)) {
    errors.email = '请输入有效的邮箱地址'
    isValid = false
  }
  
  if (!isLogin.value) {
    if (!form.confirmPassword) {
      errors.confirmPassword = '请输入确认密码'
      isValid = false
    } else if (form.password !== form.confirmPassword) {
      errors.confirmPassword = '两次输入的密码不一致'
      isValid = false
    }
  } else {
    if (!form.emailCode) {
      errors.emailCode = '请输入邮箱验证码'
      isValid = false
    }
  }
  
  return isValid
}

const API_BASE_URL = '/api/v1'

const toggleMode = () => {
  isLogin.value = !isLogin.value
  clearError()
}

const sendCode = async () => {
  if (!form.email) {
    error.value = '请输入邮箱'
    return
  }
  
  isSendingCode.value = true
  error.value = ''
  
  try {
    const response = await fetch(`${API_BASE_URL}/auth/send-code?email=${encodeURIComponent(form.email)}`, {
      method: 'POST'
    })
    
    const data = await response.json()
    if (data.success) {
      startCodeCountdown()
    } else {
      error.value = data.message || '发送验证码失败'
    }
  } catch (err) {
    error.value = '网络错误，请稍后重试'
  } finally {
    isSendingCode.value = false
  }
}

const startCodeCountdown = () => {
  codeCountdown.value = 60
  const interval = setInterval(() => {
    codeCountdown.value--
    if (codeCountdown.value <= 0) {
      clearInterval(interval)
    }
  }, 1000)
}

const submit = async () => {
  // 表单验证
  if (!form.username || !form.password || !form.email) {
    error.value = '请填写所有必填字段'
    return
  }
  
  if (!isLogin.value && form.password !== form.confirmPassword) {
    error.value = '两次输入的密码不一致'
    return
  }
  
  if (isLogin.value && !form.emailCode) {
    error.value = '请输入邮箱验证码'
    return
  }
  
  isSubmitting.value = true
  error.value = ''
  
  try {
    const endpoint = isLogin.value ? 'login' : 'register'
    const payload = isLogin.value 
      ? { username: form.username, password: form.password, email_code: form.emailCode }
      : { username: form.username, password: form.password, confirm_password: form.confirmPassword, email: form.email }
    
    const response = await fetch(`${API_BASE_URL}/auth/${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    })
    
    const data = await response.json()
    if (data.success) {
      if (isLogin.value) {
        // 登录成功，存储用户信息
        localStorage.setItem('user', JSON.stringify(data.data))
        localStorage.setItem('isLoggedIn', 'true')
        emit('login-success', data.data)
        emit('close')
      } else {
        // 注册成功，跳转到登录界面
        isLogin.value = true
        error.value = '注册成功，请登录'
      }
    } else {
      error.value = data.message || '操作失败'
    }
  } catch (err) {
    error.value = '网络错误，请稍后重试'
  } finally {
    isSubmitting.value = false
  }
}
</script>

<style scoped>
/* 右侧背景动画 */
.bg-gradient-to-br {
  position: relative;
  overflow: hidden;
}

.bg-gradient-to-br::before {
  content: '';
  position: absolute;
  top: -50%;
  right: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0) 70%);
  animation: pulse 6s ease-in-out infinite;
}

/* 卡片整体动画 */
.bg-white {
  animation: fadeInUp 0.5s ease-out;
}
</style>