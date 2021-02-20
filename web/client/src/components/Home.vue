<template>
  <body>
    <table>
      <tr>
        <td>
          <div class="sidebar">
              <div id="wiki-families">
                  <!-- Checkboxes list -->
                <div v-for='elem in projectFamilies' :key="elem">
                  <input type='checkbox' v-bind:value='elem' v-model='checkedProjectFamilies'
                         @change='updateCheckallProjects()'> {{ elem }}
                </div>
                  <!-- Check All -->
                <input type='checkbox' @click='checkAllProjects()'
                       v-model='projectFamiliesCheckAll' :disabled="projectFamiliesCheckAll == 1"> Check All
                <input type='checkbox' @click='uncheckAllProjects()'
                       v-model='projectFamiliesUncheckAll' :disabled="projectFamiliesUncheckAll == 1"> Uncheck All
                <br />
                <span>Checked families: {{ checkedProjectFamilies }}</span>
              </div>
              <hr class="dotted">
              <div id="data-modules">
                <input type="checkbox" id="checkbox" v-model="noDataModules" />
                <label for="checkbox">Disinclude modules that look like data</label>
              </div>
          </div>
        </td>
        <td>
          <table>
            <tr v-for="item in features" :key='item[0]'>
              <td> {{item[1]}} </td>
              <td> <input type="number" step="0.01" v-model="item[2]"/> </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>


    <div class="form-control">
      <button class="button_submit" v-on:click="getFunctions">Request</button>
    </div>

    <ol>
      <li v-for="(elem, index) in entries" :key="index"> {{ elem.dbname }} - {{ elem.title }}</li>
    </ol>
  </body>
</template>

<script>

  import axios from "axios";
  import qs from "qs";
  export default {
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
        projectFamiliesCheckAll: false,
        projectFamiliesUncheckAll: true,
        projectFamilies: [
          "Wikipedia",
          "Wiktionary",
          "Wikibooks",
          "Wikiquote",
          "Wikimedia",
          "Wikinews",
          "Wikiversity",
          "Wikisource"
        ],
        checkedProjectFamilies: [],
        noDataModules: false,

        entries:[]
      }
    },
    mounted: function () {
      this.$nextTick(function () {
        this.checkAllProjects()
      })
    },
    methods: {
      getFunctions() {
        axios.get('/api/data', {
          params: {
            chosenFamilies: this.checkedProjectFamilies,
            noData: this.noDataModules
          },
          paramsSerializer: params => {
            return qs.stringify(params, { arrayFormat: 'brackets' })
          },
        })
          .then(resp => {
            alert('Request sent ' + resp.status);
            console.log(resp.data.data);
            this.entries = resp.data.data;

          })
          .catch(err => {
            alert('Request failed:'+ err);
          });
      },
      checkAllProjects: function () {
        this.projectFamiliesCheckAll = !this.projectFamiliesCheckAll;
        this.checkedProjectFamilies = []; // Check all
        for (let key in this.projectFamilies) {
          this.checkedProjectFamilies.push(this.projectFamilies[key ]);
        }
        if (this.projectFamiliesUncheckAll === true) {
          this.projectFamiliesUncheckAll = !this.projectFamiliesUncheckAll;
        }
      },
      uncheckAllProjects: function () {
        this.projectFamiliesUncheckAll = !this.projectFamiliesUncheckAll;
        this.checkedProjectFamilies = [];
        if (this.projectFamiliesCheckAll === true) {
          this.projectFamiliesCheckAll = !this.projectFamiliesCheckAll;
        }
      },
      updateCheckallProjects: function () {
        if (this.projectFamilies.length == this.checkedProjectFamilies.length) {
          this.projectFamiliesCheckAll = true;
        } else {
          this.projectFamiliesCheckAll = false;
        }
        if (this.checkedProjectFamilies.length == 0) {
          this.projectFamiliesUncheckAll = true;
        } else {
          this.projectFamiliesUncheckAll = false;
        }
      },
    }
  }
</script>

<style scoped>
  html, body {
    margin: 0;
  }
  table {
    table-layout: fixed;
  }
  hr.dotted {
    border-top: 3px dotted #bbb;
  }
  .sidebar {
    padding: 20px;
    background-color: lightcyan;
    min-height: 100%;
  }
  div#wiki-families, div#data-modules {
    text-align: left;
  }
</style>
