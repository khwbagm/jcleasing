import { createApp } from "vue";
import { createPinia } from "pinia";
import { createVuetify } from "vuetify";
import * as components from "vuetify/components";
import * as directives from "vuetify/directives";
import "@mdi/font/css/materialdesignicons.css";
import App from "./App.vue";
import router from "./router";

// Import the styles
import "./styles/main.scss";

// Create Vuetify instance
const vuetify = createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: "light",
    themes: {
      light: {
        colors: {
          primary: "#1976D2",
          secondary: "#424242",
          accent: "#82B1FF",
          error: "#FF5252",
          info: "#2196F3",
          success: "#4CAF50",
          warning: "#FFC107",
        },
      },
    },
  },
  defaults: {
    VBtn: {
      variant: "flat",
    },
  },
});

// Create Pinia store
const pinia = createPinia();

// Create and mount the app
const app = createApp(App);
app.use(vuetify);
app.use(pinia);
app.use(router);
app.mount("#app");
