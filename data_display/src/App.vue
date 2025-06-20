<template>
  <v-app>
    <v-app-bar app color="primary" dark>
      <v-toolbar-title>Apartment Units Dashboard</v-toolbar-title>
      <v-spacer></v-spacer>
      <v-btn icon @click="toggleTheme">
        <v-icon>mdi-theme-light-dark</v-icon>
      </v-btn>
    </v-app-bar>

    <v-main>
      <v-container fluid class="fill-height">
        <router-view />
      </v-container>
    </v-main>
  </v-app>
</template>

<script setup lang="ts">
import { useTheme } from 'vuetify'
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const theme = useTheme()
const router = useRouter()
const isDark = ref(false)

const toggleTheme = () => {
  isDark.value = !isDark.value
  theme.global.name.value = isDark.value ? 'dark' : 'light'
  localStorage.setItem('darkTheme', isDark.value.toString())
}

onMounted(() => {
  // Check for saved theme preference
  const darkTheme = localStorage.getItem('darkTheme') === 'true'
  if (darkTheme) {
    isDark.value = true
    theme.global.name.value = 'dark'
  }
})
</script>

<style>
html {
  overflow-y: auto !important;
}
</style>
