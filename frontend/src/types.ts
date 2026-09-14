export type TodoStatus = 'pending'|'in_progress'|'completed'
export interface Todo { content:string; status:TodoStatus }
export interface TodoResponse { session_key:string; todos:Todo[]; counts:{pending:number;in_progress:number;completed:number} }
export interface AgentEvent { type:string; run_id?:string; delta?:string; content?:string; name?:string; error?:string; input?:unknown; output?:unknown; data?:TodoResponse }
