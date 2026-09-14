import { createApp, ref, onMounted, onUnmounted } from 'vue'
import { events, getTodos } from './api'
import './style.css'

createApp({ setup() {
  const todos = ref<any[]>([]), input = ref(''), reply = ref(''), busy = ref(false), error = ref('')
  let ws: WebSocket
  const onEvent = (e: any) => { if (e.type === 'run.started') busy.value = true; if (e.type === 'message.delta') reply.value += e.delta || ''; if (e.type === 'todo.updated') todos.value = e.data.todos; if (e.type === 'run.completed' || e.type === 'run.cancelled') busy.value = false; if (e.type === 'run.failed') { busy.value = false; error.value = e.error } }
  const send = () => { const message = input.value.trim(); if (!message || busy.value) return; reply.value = ''; input.value = ''; ws.send(JSON.stringify({ type: 'run.start', message })) }
  const stop = () => ws.send(JSON.stringify({ type: 'run.cancel' }))
  onMounted(async () => { todos.value = (await getTodos('demo-session')).todos; ws = events('demo-session', onEvent) }); onUnmounted(() => ws?.close())
  return { todos, input, reply, busy, error, send, stop }
}, template: `<main><section class="shell"><header><div><small>NANOBOT · AGENT WORKSPACE</small><h1>任务执行工作台</h1></div><span>{{ busy ? '● 执行中' : '● 已连接' }}</span></header><div class="body"><section class="chat"><div class="messages"><div class="message assistant"><b>nanobot</b><div>{{ reply || '告诉 nanobot 一个需要拆解或执行的任务。' }}</div></div></div><form @submit.prevent="send"><input v-model="input" placeholder="例如：实现一个登录模块" :disabled="busy"><button type="button" v-if="busy" @click="stop">停止</button><button v-else>发送</button></form><p v-if="error" class="error">{{ error }}</p></section><aside><h2>执行计划</h2><div class="counts">{{ todos.filter(t => t.status === 'completed').length }} 完成 · {{ todos.filter(t => t.status === 'in_progress').length }} 进行中 · {{ todos.filter(t => t.status === 'pending').length }} 待办</div><div v-for="todo in todos" :key="todo.content" :class="['todo', todo.status]"><span>{{ todo.status === 'completed' ? '✓' : todo.status === 'in_progress' ? '•' : '○' }}</span>{{ todo.content }}</div></aside></div></section></main>` }).mount('#app')
