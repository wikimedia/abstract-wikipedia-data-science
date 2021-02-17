import Vue from 'vue';
import Router from 'vue-router';
import Ping from '@/components/Ping';
import Sidebar from "@/components/Sidebar";

Vue.use(Router);

export default new Router({
  routes: [
    {
      path: '/',
      name: 'Ping',
      component: Ping,
    },
    {
      path: "/side",
      name: "Sidebar",
      component: Sidebar,
    }
  ],
});