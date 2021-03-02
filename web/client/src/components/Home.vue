<template>
  <body>
    <table>
      <tr>
        <td>
          <div class="sidebar">
            <badger-accordion>
              <badger-accordion-item>
                <template slot="header">Choose wikipedia project families ▽</template>
                <template slot="content">
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
                  </div>
                </template>
              </badger-accordion-item>

              <badger-accordion-item>
                <template slot="header">Choose wikipedia project languages ▽</template>
                <template slot="content">
                  <div id="wiki-langs">
                  <!-- Checkboxes list -->
                    <div v-for='elem in projectLanguages' :key="elem">
                    <input type='checkbox' v-bind:value='elem' v-model='checkedLanguages'
                         @change='updateCheckallLangs()'> {{ elem }}
                    </div>
                  <!-- Check All -->
                    <input type='checkbox' @click='checkAllLangs()'
                       v-model='projectLangsCheckAll' :disabled="projectLangsCheckAll == 1"> Check All
                    <input type='checkbox' @click='uncheckAllProjects()'
                       v-model='projectLangsUncheckAll' :disabled="projectLangsUncheckAll == 1"> Uncheck All
                    <br />
                  </div>
                </template>
              </badger-accordion-item>

              <badger-accordion-item>
                <template slot="header">Choose whether to work with data modules ▽</template>
                <template slot="content">
                  <div id="data-modules">
                <input type="checkbox" id="checkbox" v-model="noDataModules" />
                <label for="checkbox">Disinclude modules that look like data</label>
              </div>
                </template>
              </badger-accordion-item>
            </badger-accordion>

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
      <button class="button_submit" v-on:click="getFunctions">
        {{ requestButton }}</button>
    </div>

    <div class="return_results"><ol>
      <li v-for="(elem, index) in entries" :key="index">
        <a :href="`/script/${elem.dbname}/${elem.pageid}/`">
              {{ elem.dbname }} - {{ elem.title }}</a>
      </li>
    </ol></div>
  </body>
</template>

<script>
  import {BadgerAccordion, BadgerAccordionItem} from "vue-badger-accordion";
  import axios from "axios";
  import qs from "qs";
  import families from '../../public/family.json'
  import languages from '../../public/lang.json'
  export default {
    data(){
      return {
        requestButton: "Request",

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
        projectLangsCheckAll: false,
        projectLangsUncheckAll: true,
        projectFamilies: families,
        projectLanguages: languages,

        checkedProjectFamilies: [],
        checkedLanguages: [],
        noDataModules: false,

        entries:[]
      }
    },
    mounted: function () {
      this.$nextTick(function () {
        this.checkAllProjects();
        this.checkAllLangs();
      })
    },
    components: {
        BadgerAccordion,
        BadgerAccordionItem
    },
    methods: {
      getFunctions() {
        const weights = []
        this.features.forEach(([_0, _1, value]) =>
            weights.push(value))

        this.requestButton = "Loading..."
        axios.get('/api/data', {
          params: {
            chosenFamilies: this.checkedProjectFamilies,
            noData: this.noDataModules,
            weights: weights,
          },
          paramsSerializer: params => {
            return qs.stringify(params, { arrayFormat: 'brackets' })
          },
        })
          .then(resp => {
            this.entries = JSON.parse(resp.data.data);
            this.requestButton = "Request"

          })
          .catch(err => {
            alert('Request failed:'+ err);
            this.requestButton = "Request"
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

      checkAllLangs: function () {
        this.projectLangsCheckAll = !this.projectLangsCheckAll;
        this.checkedLanguages = []; // Check all
        for (let key in this.projectLanguages) {
          this.checkedLanguages.push(this.projectLanguages[key ]);
        }
        if (this.projectLangsUncheckAll === true) {
          this.projectLangsUncheckAll = !this.projectLangsUncheckAll;
        }
      },
      uncheckAllLangs: function () {
        this.projectLangsUncheckAll = !this.projectLangsUncheckAll;
        this.checkedLanguages = [];
        if (this.projectLangsCheckAll === true) {
          this.projectLangsCheckAll = !this.projectLangsCheckAll;
        }
      },
      updateCheckallLangs: function () {
        if (this.projectLanguages.length == this.checkedLanguages.length) {
          this.projectLangsCheckAll = true;
        } else {
          this.projectLangsCheckAll = false;
        }
        if (this.checkedLanguages.length == 0) {
          this.projectLangsUncheckAll = true;
        } else {
          this.projectLangsUncheckAll = false;
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
  .sidebar {
    padding: 20px;
    background-color: lightcyan;
    min-height: 100%;
  }
  div#wiki-families, div#data-modules {
    text-align: left;
  }
  .badger-accordion__header .js-badger-accordion-header .badger-accordion-toggle {
    font-family: Avenir, Helvetica, Arial, sans-serif;
    font-size: large !important;
  }
  .return_results {
    text-align: left;
    padding: 30px;
  }
</style>
