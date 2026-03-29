import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './styles/main.css'
import { useBuildStore } from '@/stores/build'
import { useProfessionTalentStore } from '@/stores/professionTalent'

const app = createApp(App)
const pinia = createPinia()
app.use(pinia)
app.use(router)

const buildStore = useBuildStore()
const professionStore = useProfessionTalentStore()
professionStore.applyFromPersistedBuild(buildStore.snapshot.talent)

app.mount('#app')
