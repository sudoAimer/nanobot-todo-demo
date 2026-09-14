export type TodoStatus = 'pending'|'in_progress'|'completed'
export interface Todo { content:string; status:TodoStatus }
export interface TodoResponse { session_key:string; todos:Todo[]; counts:{pending:number;in_progress:number;completed:number} }
