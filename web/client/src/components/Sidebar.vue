<template>
  <tbody>
    <div id="wiki-families">
        <!-- Checkboxes list -->
      <span v-for='elem in projectFamilies' :key="elem">
        <input type='checkbox' v-bind:value='elem' v-model='checkedProjectFamilies'
               @change='updateCheckallProjects()'> {{ elem }}
      </span>
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
      <label for="checkbox">Disinclude modules that look like data</label>
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