import { Component, type ErrorInfo, type ReactNode } from "react";
export class ErrorBoundary extends Component<{children:ReactNode},{error:boolean}>{
 state={error:false};
 static getDerivedStateFromError(){return{error:true}}
 componentDidCatch(error:Error,info:ErrorInfo){console.error("Swift UI error",error,info)}
 render(){return this.state.error?<main className="not-found"><h1>Something went wrong</h1><p>The Swift workspace could not render this view.</p><button className="btn" onClick={()=>location.reload()}>Reload application</button></main>:this.props.children}
}
