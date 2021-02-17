<template>
  <tbody>
    <div id="wiki-families">
        <!-- Checkboxes list -->
      <ul>
        <li v-for='elem in projectFamilies' :key="elem">
          <input type='checkbox' v-bind:value='elem' v-model='checkedProjectFamilies'
                 @change='updateCheckallProjects()'> {{ elem }}
        </li>
      </ul>

      <!--
      <input type="checkbox" id="wiki" value="Wikipedia" v-model="projectFamilies" />
      <label for="wiki">Wikipedia</label>
      <input type="checkbox" id="wiktionary" value="Wiktionary" v-model="projectFamilies" />
      <label for="wiktionary">Wiktionary</label>
      <input type="checkbox" id="wikibooks" value="Wikibooks" v-model="projectFamilies" />
      <label for="wikibooks">Wikibooks</label>
      <input type="checkbox" id="wikiquote" value="Wikiquote" v-model="projectFamilies" />
      <label for="wikiquote">Wikiquote</label>
      <input type="checkbox" id="wikimedia" value="Wikimedia" v-model="projectFamilies" />
      <label for="wikimedia">Wikimedia</label>
      <input type="checkbox" id="wikinews" value="Wikinews" v-model="projectFamilies" />
      <label for="wikinews">Wikinews</label>
      <input type="checkbox" id="wikiversity" value="Wikiversity" v-model="projectFamilies" />
      <label for="wikiversity">Wikiversity</label>
      <input type="checkbox" id="wikisource" value="Wikisource" v-model="projectFamilies" />
      <label for="wikisource">Wikisource</label>
      -->
        <!-- Check All -->
      <input type='checkbox' @click='checkAllProjects()'
             v-model='projectFamiliesCheckAll' :disabled="projectFamiliesCheckAll == 1"> Check All
      <input type='checkbox' @click='uncheckAllProjects()'
             v-model='projectFamiliesUncheckAll' :disabled="projectFamiliesUncheckAll == 1"> Uncheck All
      <br />
      <span>Checked families: {{ checkedProjectFamilies }}</span>
    </div>
    <div id="data-modules">
      <input type="checkbox" id="checkbox" v-model="noDataModules" />
      <label for="checkbox">{{ noDataModules }}</label>
    </div>
  </tbody>
</template>

<script>
export default {
  name: "Sidebar",
  data() {
    return {
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
      noDataModules: false
    }
  },

  methods: {
    checkAllProjects: function () {
      this.projectFamiliesCheckAll = !this.projectFamiliesCheckAll;
      this.checkedProjectFamilies = []; // Check all
      for (let key in this.projectFamilies) {
        this.checkedProjectFamilies.push(this.projectFamilies[key]);
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

</style>