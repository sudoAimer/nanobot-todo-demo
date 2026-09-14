<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { events, getTodos } from './api'
import type { AgentEvent, Todo } from './types'
const todos = ref<Todo[]>([])
const input = ref('')
const reply = ref('')
const busy = ref(false)
const error = ref('')
let socket: WebSocket
function onEvent(event: AgentEvent) {
  if (event.type === 'run.started') busy.value = true
  if (event.type === 'message.delta') reply.value += event.delta || ''
  if (event.type === 'todo.updated' && event.data) todos.value = event.data.todos
  if (event.type === 'run.completed' || event.type === 'run.cancelled') busy.value = false
  if (event.type === 'run.failed') { busy.value = false; error.value = event.error || '运行失败' }
}
function send() { const message = input.value.trim(); if (!message || busy.value) return; reply.value = ''; input.value = ''; socket.send(JSON.stringify({ type: 'run.start', message })) }
function stop() { socket.send(JSON.stringify({ type: 'run.cancel' })) }
onMounted(async () => { todos.value = (await getTodos('demo-session')).todos; socket = events('demo-session', onEvent) })
onUnmounted(() => socket?.close())
</script>
<template>
  <main><section class="shell"><header><div><small>NANOBOT · AGENT WORKSPACE</small><h1>任务执行工作台</h1></div><span>{{ busy ? '● 执行中' : '● 已连接' }}</span></header>
  <div class="body"><section class="chat"><div class="messages"><div class="message assistant"><b>nanobot</b><div>{{ reply || '告诉 nanobot 一个需要拆解或执行的任务。' }}</div></div></div><form @submit.prevent="send"><input v-model="input" placeholder="例如：实现一个登录模块" :disabled="busy"><button type="button" v-if="busy" @click="stop">停止</button><button v-else>发送</button></form><p v-if="error" class="error">{{ error }}</p></section>
  <aside><h2>执行计划</h2><div class="counts">{{ todos.filter(t => t.status === 'completed').length }} 完成 · {{ todos.filter(t => t.status === 'in_progress').length }} 进行中 · {{ todos.filter(t => t.status === 'pending').length }} 待办</div><div v-for="todo in todos" :key="todo.content" :class="['todo', todo.status]"><span>{{ todo.status === 'completed' ? '✓' : todo.status === 'in_progress' ? '•' : '○' }}</span>{{ todo.content }}</div></aside></div></section></main>
</template>
