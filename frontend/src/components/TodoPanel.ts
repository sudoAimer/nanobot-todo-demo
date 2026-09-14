import { h, type Ref } from 'vue'
import './TodoPanel.css'
import './TodoPanel.compact.css'

const icon = (status: string) => status === 'completed'
  ? h('svg', { class: 'todo-svg completed', width: 14, height: 14, viewBox: '0 0 14 14', fill: 'none' }, [h('circle', { cx: 7, cy: 7, r: 6.4, stroke: 'currentColor', 'stroke-width': 1.2 }), h('path', { d: 'M10.9631 5.71411L7.70154 8.97571C7.48011 9.19714 7.27736 9.40099 7.09229 9.54993C6.89742 9.70669 6.66314 9.85279 6.3634 9.90027C6.2049 9.92534 6.04339 9.92534 5.88489 9.90027C5.58515 9.85279 5.35087 9.70669 5.15601 9.54993C4.97093 9.40099 4.76818 9.19714 4.54675 8.97571L3.03516 7.46411L3.96313 6.53613L5.47473 8.04773C5.7169 8.28989 5.86196 8.43389 5.97888 8.52795C6.08597 8.61409 6.10875 8.60701 6.08997 8.604C6.11259 8.60758 6.13571 8.60758 6.15833 8.604C6.13954 8.60701 6.16232 8.61409 6.26941 8.52795C6.38633 8.43389 6.53139 8.28989 6.77356 8.04773L10.0352 4.78613L10.9631 5.71411Z', fill: 'currentColor' })])
  : h('svg', { class: ['todo-svg', status], width: 14, height: 14, viewBox: '0 0 14 14', fill: 'none' }, [h('circle', { cx: 7, cy: 7, r: 6.4, stroke: 'currentColor', 'stroke-width': 1.2, ...(status === 'pending' ? { 'stroke-dasharray': '2.4 2.4' } : {}) })])

export function TodoPanel(todos: Ref<any[]>, open: Ref<boolean>, toggle: () => void) {
  const completed = () => todos.value.filter(x => x.status === 'completed').length
  const active = () => todos.value.filter(x => x.status === 'in_progress').length
  const pending = () => todos.value.filter(x => x.status === 'pending').length
  return h('div', { class: ['todo-panel', open.value ? 'is-open' : 'is-collapsed'] }, [
    h('button', { class: 'todo-panel-header', onClick: toggle }, [
      h('span', { class: 'todo-panel-label' }, '任务'),
      h('span', { class: 'todo-panel-meta' }, `${completed()} 已完成 · ${active()} 进行中 · ${pending()} 待处理  ${open.value ? '⌄' : '⌃'}`),
    ]),
    open.value && h('div', { class: 'todo-panel-body' }, todos.value.map(todo => h('div', { class: ['todo-row', todo.status], key: todo.content }, [icon(todo.status), h('span', `${todo.content}（${todo.status === 'completed' ? '已完成' : todo.status === 'in_progress' ? '进行中' : '待开始'}）`)]))),
  ])
}
