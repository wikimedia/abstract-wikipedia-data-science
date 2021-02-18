<template>
  <body>
    <div class="sidebar">
      <Sidebar/>
    </div>
  </body>
</template>

<script>
  import Sidebar from "@/components/Sidebar"
  export default {
    components: {
      Sidebar
    }
  }
</script>

<style scoped>
  html, body {
    margin: 0;
  }
</style>