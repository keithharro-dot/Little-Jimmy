// Test stand-in for PeerJS: pages in the same browser context talk over a BroadcastChannel instead of WebRTC.
// Routed in place of peerjs.min.js by tests/smoke.mjs. Not used by the games themselves.
class MockConn{constructor(p,remote){this.p=p;this.remote=remote;this.h={};this.open=false}
on(e,f){this.h[e]=f}_emit(e,a){this.h[e]&&this.h[e](a)}_open(){this.open=true;this._emit('open')}
send(d){if(this.open)this.p.bc.postMessage({type:'data',from:this.p.id,to:this.remote,d:JSON.parse(JSON.stringify(d))})}
close(){if(!this.open)return;this.open=false;this.p.bc.postMessage({type:'close',from:this.p.id,to:this.remote});this._emit('close')}}
window.Peer=class{constructor(id){if(typeof id==='object')id=undefined;this.id=id||'g'+Math.random();this.h={};this.conns={};this.bc=new BroadcastChannel('mock');this.bc.onmessage=e=>this._msg(e.data);setTimeout(()=>this._emit('open',this.id),50)}
on(e,f){this.h[e]=f}_emit(e,a){this.h[e]&&this.h[e](a)}
connect(t){const c=new MockConn(this,t);this.conns[t]=c;this.bc.postMessage({type:'connect',from:this.id,to:t});return c}
_msg(m){if(this.destroyed||m.to!==this.id)return;const c0=this.conns[m.from];if(m.type==='connect'){const c=new MockConn(this,m.from);this.conns[m.from]=c;this._emit('connection',c);this.bc.postMessage({type:'accept',from:this.id,to:m.from});setTimeout(()=>c._open(),10)}
else if(m.type==='accept')c0._open();else if(m.type==='data'&&c0)c0._emit('data',m.d);else if(m.type==='close'&&c0&&c0.open){c0.open=false;c0._emit('close')}}
destroy(){for(const c of Object.values(this.conns))c.close();this.destroyed=true}reconnect(){}}
