<template>
  <body>
    <div class="sidebar">
      <Sidebar/>
    </div>
    <table>
    <tr v-for="item in features" :key='item[0]'>
        <td>
          {{item[1]}}
        </td>
        <td>
          {{item[2]}}
        </td>
        <td>
          <input type="number" step="0.01" v-model="item[2]"/>
        </td>
    </tr>
  </table>
    <div class="form-control">
      <button class="button_submit" v-on:click="getFunctions">Request</button>
    </div>
  </body>
</template>

<script>
  import Sidebar from "@/components/Sidebar"
  import axios from "axios";
  export default {
    components: {
      Sidebar
    },
    data(){
      return {
        features: [
          ["edits_per_editor_score", "Edits per editor score", 1],
          ["edits_per_day_score", "Edits per day score", 1],
          ["length_score", "Length score", 0.1],
          ["langs_score", "Language links score", 5],
          ["editors_norm_score", "Unique editors normalized score", 2],
          ["major_edits_norm_score", "Amount of major edits normalized score", 5],
          ["pls_norm_score", "Amount of pagelinks normalized score", 2],
          ["transcluded_in_norm_score", "Amount of transclusions normalized score", 8],
        ],
      }
    },
    methods: {
      getFunctions() {
        axios.post('http://localhost:5000/api/')
          .then(response => response.json())
          .then(resp => {
            alert('Request sent');
          })
          .catch(() => {
            alert('Request failed');
          });
      }
    }
  }
</script>

<style scoped>
  html, body {
    margin: 0;
  }
</style>