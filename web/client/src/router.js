import Vue from 'vue';
import Router from 'vue-router';
import Home from "@/components/Home";
import PageNotFound from "@/components/PageNotFound";
import ScriptPage from "@/components/ScriptPage";

Vue.use(Router);

export default new Router({
  mode: "history",
  routes: [
    {
      path: '/',
      name: 'Home',
      component: Home,
    },
    {
      path: "/script/:dbname/:pageid",
      name: "ScriptPage",
      component: ScriptPage,
    },
    {
      path: "/:pathMatch(.*)*",
      name: "PageNotFound",
      component: PageNotFound,
    }
  ],
});