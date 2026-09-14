import type { TodoResponse } from './types'
const base='http://localhost:8000'
export async function getTodos(session:string):Promise<TodoResponse>{return (await fetch(`${base}/api/sessions/${session}/todos`)).json()}
export async function chat(session:string,message:string){return (await fetch(`${base}/api/sessions/${session}/chat`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message})})).json()}
export function events(session:string){return new WebSocket(`${base.replace('http','ws')}/api/sessions/${session}/events`)}
