import './style.css'
import { App } from './ui/app'

const container = document.getElementById('app')
if (!container) throw new Error('#app not found')

const app = new App(container)

window.addEventListener('resize', () => { /* auto-resize handled by CSS */ })
window.addEventListener('beforeunload', () => app.destroy())
