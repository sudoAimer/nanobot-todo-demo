<script setup>
import { onMounted, ref } from 'vue'; import { chat, events, getTodos } from './api'
const session='demo-session', todos=ref([]), input=ref(''), reply=ref(''), busy=ref(false), error=ref('')
const counts=()=>({pending:todos.value.filter(x=>x.status==='pending').length,in_progress:todos.value.filter(x=>x.status==='in_progress').length,completed:todos.value.filter(x=>x.status==='completed').length})
async function send(){if(!input.value.trim()||busy.value)return; busy.value=true; error.value=''; const msg=input.value; input.value=''; try{const r=await chat(session,msg); reply.value=r.content; todos.value=r.todos}catch(e){error.value=String(e)}finally{busy.value=false}}
onMounted(async()=>{todos.value=(await getTodos(session)).todos; const ws=events(session); ws.onmessage=e=>{const v=JSON.parse(e.data); if(v.type==='todo.updated')todos.value=v.data.todos}})
</script>
<template><main><section class="chat"><h1>nanobot Todo Demo</h1><div class="bubble">{{reply||'告诉 nanobot 一个需要拆解的任务。'}}</div><form @submit.prevent="send"><input v-model="input" placeholder="例如：实现一个登录模块"/><button :disabled="busy">{{busy?'运行中…':'发送'}}</button></form><p v-if="error" class="error">{{error}}</p></section><aside><h2>任务清单</h2><div class="counts">待办 {{counts().pending}} · 进行中 {{counts().in_progress}} · 完成 {{counts().completed}}</div><div v-for="todo in todos" :key="todo.content" class="todo" :class="todo.status"><span>{{todo.status==='completed'?'✓':todo.status==='in_progress'?'•':'○'}}</span>{{todo.content}}</div><p v-if="!todos.length" class="muted">暂无任务</p></aside></main></template>
