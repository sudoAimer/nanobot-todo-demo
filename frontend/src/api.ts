import type { TodoResponse, AgentEvent } from './types'
const base=import.meta.env.VITE_API_URL||'http://localhost:8000'
export async function getTodos(session:string):Promise<TodoResponse>{return (await fetch(`${base}/api/sessions/${session}/todos`)).json()}
export function events(session:string,onEvent:(e:AgentEvent)=>void){const ws=new WebSocket(`${base.replace(/^http/,'ws')}/api/sessions/${session}/ws`);ws.onmessage=e=>onEvent(JSON.parse(e.data));return ws}
