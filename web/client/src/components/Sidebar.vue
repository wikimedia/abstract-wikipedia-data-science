<template>
  <tbody>
    <div id="wiki-families">
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
      <br />
      <span>Checked families: {{ projectFamilies }}</span>
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
      projectFamilies: [],
      noDataModules: false
    }
  }
}
</script>

<style scoped>

</style>