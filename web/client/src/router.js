import Vue from 'vue';
import Router from 'vue-router';
import Ping from '@/components/Ping';
import Sidebar from "@/components/Sidebar";
import Home from "@/components/Home";
import PageNotFound from "@/components/PageNotFound";

Vue.use(Router);

export default new Router({
  routes: [
    {
      path: '/',
      name: 'Home',
      component: Home,
    },
    {
      path: "/side",
      name: "Sidebar",
      component: Sidebar,
    },
    {
      path: "/:pathMatch(.*)*",
      name: "Page Not Found",
      component: PageNotFound,
    }
  ],
});