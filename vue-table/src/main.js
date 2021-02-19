import Vue from 'vue'
import App from './App.vue'
import BootstrapVue from 'bootstrap-vue'
import ToggleSwitch from 'vuejs-toggle-switch'
import fullscreen from 'vue-fullscreen'
import VueMqtt from 'vue-mqtt'
import {CONFIG} from "./config.js"

Vue.use(VueMqtt, CONFIG.WS_SERVER, {clientId: 'WebClient-' + parseInt(Math.random() * 100000)})
Vue.use(ToggleSwitch);
Vue.use(BootstrapVue);
Vue.use(fullscreen);

import 'bootstrap/dist/css/bootstrap.css'
import 'bootstrap-vue/dist/bootstrap-vue.css'
import "vue-material-design-icons/styles.css"

new Vue({
  el: '#app',
  render: h => h(App)
})
