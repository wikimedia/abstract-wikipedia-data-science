<template>
  <body>
    <div class="script_title">
      {{ script.title }}
    </div>
    <div class="script_identity">
      From {{ script.dbname }}: page id {{ script.pageid }}
    </div>
    <table> <tr>
      <td>
        <code class="script_code"> {{ script.sourcecode }} </code>
      </td>
      <td>
        <div id="cluster_entries">
          Similar entries
          <div v-for='(elem, i) in script.similarItems' :key="i">
            <a :href="`/${elem.dbname}/${elem.pageid}/`">
              {{ elem.dbname }} - {{ elem.title }}</a>
          </div>
        </div>
      </td>
    </tr>
    </table>
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
    methods: {
      loadData () {
        let dbname = this.$route.params.dbname;
        let pageid = this.$route.params.pageid;
        axios.get('http://127.0.0.1:5000/api/'+ dbname + '/' + pageid).then(resp => {
          if (resp.data.status == 'success') {
            this.script = JSON.parse(resp.data.data);
            this.script.similarItems = JSON.parse(resp.data.cluster);
            console.log(this.script.similarItems)
          }
          else {
            this.$router.push( { name: "PageNotFound"})
          }

        })
        .catch(err => {
          alert('Request failed:'+ err);
        });
      }
    },
    mounted() {
      this.loadData();
    },
  }
</script>

<style scoped>
  .script_code {
    white-space: pre-wrap;
    background-color: #eee;
    border: 1px solid #999;
    display: block;
    text-align: left;
    padding: 20px;
  }
  td {
    vertical-align: top;
    padding: 20px;
  }
</style>