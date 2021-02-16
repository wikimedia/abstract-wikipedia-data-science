<template>
    <div id="app">
        <ul>
            <li>{{ answer }}</li>
        </ul>
    </div>
</template>
<script>
    import axios from 'axios'

    export default {
        name: 'app',
        data() {
            return {
                    answer: "no"
            }
        },
        created() {
          axios.get("/ping").then(r => {
            this.answer = r.data
          })
        }
    }
</script>
<style scoped>

</style>