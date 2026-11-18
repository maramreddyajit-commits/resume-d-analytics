import {render as churniq} from './churniq.js';
import {render as experimentlab} from './experimentlab.js';
import {render as marketscope} from './marketscope.js';
import {render as demandcast} from './demandcast.js';
const routes={churniq,experimentlab,marketscope,demandcast};async function run(){const key=location.hash.slice(1)||'churniq';document.querySelector('#app').textContent='Loading verified results…';try{await (routes[key]||churniq)();for(const a of document.querySelectorAll('nav a')){a.removeAttribute('aria-current');if(a.hash==='#'+key)a.setAttribute('aria-current','page');}}catch(e){document.querySelector('#app').innerHTML='<div class="notice error" role="alert"></div>';document.querySelector('[role=alert]').textContent=e.message;}}addEventListener('hashchange',run);run();
