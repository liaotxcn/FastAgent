<template>
  <div v-if="isVisible" class="fixed inset-0 bg-gradient-to-br from-blue-50 to-blue-100 z-50 flex items-center justify-center p-4 transition-opacity duration-300">
    <div class="bg-white rounded-2xl shadow-2xl w-full max-w-5xl overflow-hidden">
      <div class="flex flex-col md:flex-row">
        <!-- 左侧：表单区域 -->
        <div class="w-full md:w-1/2 p-8 md:p-12 flex flex-col">
          <!-- 标题 -->
          <div class="mb-10">
            <h1 class="text-3xl font-bold text-gray-800 mb-2">FastAgent</h1>
            <p class="text-gray-500">智能助手</p>
          </div>
          
          <!-- 切换标签 -->
          <div class="flex mb-8">
            <button 
              @click="isLogin = true" 
              class="px-4 py-2 text-lg font-medium transition-colors border-b-2" 
              :class="isLogin ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'"
            >
              登录
            </button>
            <button 
              @click="isLogin = false" 
              class="px-4 py-2 text-lg font-medium transition-colors border-b-2" 
              :class="!isLogin ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'"
            >
              注册
            </button>
          </div>
          
          <!-- 登录表单 -->
          <div v-show="isLogin" class="space-y-6 flex-grow">
            <!-- 用户名 -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">用户名</label>
              <input 
                v-model="form.username" 
                type="text" 
                class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all duration-200"
                placeholder="请输入用户名"
                @input="clearError"
              />
              <div v-if="errors.username" class="text-red-500 text-xs mt-1">{{ errors.username }}</div>
            </div>
            
            <!-- 密码 -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">密码</label>
              <div class="relative">
                <input 
                  v-model="form.password" 
                  :type="showPassword ? 'text' : 'password'" 
                  class="w-full px-4 py-3 pr-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all duration-200"
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
              <div v-if="errors.password" class="text-red-500 text-xs mt-1">{{ errors.password }}</div>
            </div>
            
            <!-- 邮箱 -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">邮箱</label>
              <div class="flex gap-2">
                <input 
                  v-model="form.email" 
                  type="email" 
                  class="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all duration-200"
                  placeholder="请输入邮箱"
                  @input="clearError"
                />
                <button 
                  @click="sendCode" 
                  :disabled="isSendingCode" 
                  class="px-4 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-all duration-200 whitespace-nowrap"
                >
                  {{ isSendingCode ? '发送中...' : codeCountdown > 0 ? `${codeCountdown}s` : '发送验证码' }}
                </button>
              </div>
              <div v-if="errors.email" class="text-red-500 text-xs mt-1">{{ errors.email }}</div>
            </div>
            
            <!-- 邮箱验证码 -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">邮箱验证码</label>
              <input 
                v-model="form.emailCode" 
                type="text" 
                class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all duration-200"
                placeholder="请输入验证码"
                @input="clearError"
              />
              <div v-if="errors.emailCode" class="text-red-500 text-xs mt-1">{{ errors.emailCode }}</div>
            </div>
            
            <!-- 错误信息 -->
            <div v-if="error" :class="error === '注册成功，请登录' ? 'text-green-500 text-sm p-3 bg-green-50 rounded-lg animate-fadeIn' : 'text-red-500 text-sm p-3 bg-red-50 rounded-lg animate-fadeIn'">
              {{ error }}
            </div>
            
            <!-- 提交按钮 -->
            <button 
              @click="submit" 
              :disabled="isSubmitting" 
              class="w-full py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white rounded-lg font-medium transition-all duration-300 shadow-lg shadow-blue-500/25 disabled:shadow-none mt-4"
            >
              {{ isSubmitting ? '处理中...' : '登录' }}
            </button>
          </div>
          
          <!-- 注册表单 -->
          <div v-show="!isLogin" class="space-y-6 flex-grow">
            <!-- 用户名 -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">用户名</label>
              <input 
                v-model="form.username" 
                type="text" 
                class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all duration-200"
                placeholder="请输入用户名"
                @input="clearError"
              />
              <div v-if="errors.username" class="text-red-500 text-xs mt-1">{{ errors.username }}</div>
            </div>
            
            <!-- 密码 -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">密码</label>
              <div class="relative">
                <input 
                  v-model="form.password" 
                  :type="showPassword ? 'text' : 'password'" 
                  class="w-full px-4 py-3 pr-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all duration-200"
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
              <div v-if="errors.password" class="text-red-500 text-xs mt-1">{{ errors.password }}</div>
            </div>
            
            <!-- 确认密码 -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">确认密码</label>
              <div class="relative">
                <input 
                  v-model="form.confirmPassword" 
                  :type="showPassword ? 'text' : 'password'" 
                  class="w-full px-4 py-3 pr-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all duration-200"
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
              <div v-if="errors.confirmPassword" class="text-red-500 text-xs mt-1">{{ errors.confirmPassword }}</div>
            </div>
            
            <!-- 邮箱 -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">邮箱</label>
              <input 
                v-model="form.email" 
                type="email" 
                class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all duration-200"
                placeholder="请输入邮箱"
                @input="clearError"
              />
              <div v-if="errors.email" class="text-red-500 text-xs mt-1">{{ errors.email }}</div>
            </div>
            
            <!-- 错误信息 -->
            <div v-if="error" class="text-red-500 text-sm p-3 bg-red-50 rounded-lg animate-fadeIn">
              {{ error }}
            </div>
            
            <!-- 提交按钮 -->
            <button 
              @click="submit" 
              :disabled="isSubmitting" 
              class="w-full py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white rounded-lg font-medium transition-all duration-300 shadow-lg shadow-blue-500/25 disabled:shadow-none mt-4"
            >
              {{ isSubmitting ? '处理中...' : '注册' }}
            </button>
          </div>
        </div>
        
        <!-- 右侧：图片区域 -->
        <div class="hidden md:block w-1/2 bg-blue-500 p-12 flex flex-col justify-center">
          <div class="text-white space-y-6">
            <h2 class="text-3xl font-bold">Let's embark on this fun experience together</h2>
            <p class="text-blue-100 text-lg">Using FastAgent to build a smarter and better world, we believe</p>
            <div class="mt-8 flex justify-center">
              <img src="/src/logo.png" alt="FastAgent" class="w-40 h-40 object-contain" />
            </div>
            <div class="mt-8 grid grid-cols-2 gap-6">
              <div class="flex items-center gap-4">
                <div class="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center">
                  <i class="fa fa-comments text-white text-2xl"></i>
                </div>
                <span class="text-white text-lg">智能问答</span>
              </div>
              <div class="flex items-center gap-4">
                <div class="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center">
                  <i class="fa fa-search text-white text-2xl"></i>
                </div>
                <span class="text-white text-lg">信息检索</span>
              </div>
              <div class="flex items-center gap-4">
                <div class="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center">
                  <i class="fa fa-image text-white text-2xl"></i>
                </div>
                <span class="text-white text-lg">图片分析</span>
              </div>
              <div class="flex items-center gap-4">
                <div class="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center">
                  <i class="fa fa-map-marker text-white text-2xl"></i>
                </div>
                <span class="text-white text-lg">位置导航</span>
              </div>
              <div class="flex items-center gap-4">
                <div class="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center">
                  <i class="fa fa-database text-white text-2xl"></i>
                </div>
                <span class="text-white text-lg">数据查询</span>
              </div>
              <div class="flex items-center gap-4">
                <div class="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center">
                  <i class="fa fa-tasks text-white text-2xl"></i>
                </div>
                <span class="text-white text-lg">事务处理</span>
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
/* 动画效果 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 表单输入动画 */
input {
  transition: all 0.3s ease;
}

input:focus {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
}

/* 按钮动画 */
button {
  transition: all 0.3s ease;
}

button:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);
}

button:active:not(:disabled) {
  transform: translateY(0);
}

/* 标签切换动画 */
button[class*="border-blue-500"] {
  transition: all 0.3s ease;
}

/* 整体容器动画 */
.bg-white {
  animation: fadeInUp 0.5s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 右侧背景装饰 */
.bg-blue-500 {
  position: relative;
  overflow: hidden;
}

.bg-blue-500::before {
  content: '';
  position: absolute;
  top: -50%;
  right: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0) 70%);
  animation: pulse 6s ease-in-out infinite;
}

@keyframes pulse {
  0% {
    transform: scale(1);
    opacity: 0.5;
  }
  50% {
    transform: scale(1.1);
    opacity: 0.8;
  }
  100% {
    transform: scale(1);
    opacity: 0.5;
  }
}
</style>