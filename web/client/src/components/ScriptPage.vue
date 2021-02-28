<template>
  <body>
    <div class="script_title">
      {{ script.title }}
    </div>
    <div class="script_identity">
      From {{ script.dbname }}: page id {{ script.pageid }}
    </div>
    <code class="script_code">
      {{ script.sourcecode }}
    </code>
  </body>
</template>

<script>
  import axios from "axios";

  export default {
    name: "ScriptPage",
    data(){
      return {
        script: {
          pageid: 0,
          dbname: "None",
          title: "None",
          sourcecode: "None",
          similarItems: []
        }
      }
    },

    mounted: function () {
      let dbname = this.$route.params.dbname;
      let pageid = this.$route.params.pageid;
      axios.get('api/'+ dbname + '/' + pageid).then(resp => {
        if (resp.data.status == 'success') {
          this.script = JSON.parse(resp.data.data);
        }
        else {
          this.$router.push( { name: "PageNotFound"})
        }

      })
      .catch(err => {
        alert('Request failed:'+ err);
      });
    },
  }
</script>

<style scoped>
  .script_code {
    white-space: pre-wrap;
    background-color: #eee;
    border: 1px solid #999;
    display: block;
    padding: 20px;
  }
</style>