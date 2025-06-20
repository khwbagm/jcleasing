<template>
  <v-container fluid class="fill-height pa-0">
    <v-row no-gutters class="fill-height">
      <!-- Filters Sidebar -->
      <v-col cols="12" md="3" class="pr-md-2">
        <v-card class="h-100" :elevation="2">
          <v-card-title class="d-flex justify-space-between align-center">
            <span>Filters</span>
            <v-btn
              variant="text"
              color="primary"
              size="small"
              @click="unitStore.resetFilters"
            >
              Reset
            </v-btn>
          </v-card-title>

          <v-card-text>
            <!-- Search -->
            <v-text-field
              v-model="filters.searchQuery"
              label="Search"
              prepend-inner-icon="mdi-magnify"
              variant="outlined"
              density="compact"
              hide-details
              class="mb-4"
            />

            <!-- Building Filter -->
            <v-select
              v-model="filters.building"
              :items="unitStore.availableBuildings"
              label="Building"
              multiple
              variant="outlined"
              density="comfortable"
              hide-details
              class="mb-4"
              chips
              clearable
            />

            <!-- Floorplan Type Filter -->
            <v-select
              v-model="filters.floorplanType"
              :items="unitStore.availableFloorplanTypes"
              label="Floorplan Type"
              multiple
              variant="outlined"
              density="comfortable"
              hide-details
              class="mb-4"
              chips
              clearable
            />

            <!-- Price Range -->
            <div class="text-subtitle-2 text-medium-emphasis mb-2">
              Price Range
            </div>
            <v-row no-gutters class="mb-4">
              <v-col cols="6" class="pr-1">
                <v-text-field
                  v-model.number="filters.minPrice"
                  label="Min"
                  type="number"
                  variant="outlined"
                  density="compact"
                  hide-details
                  placeholder="Min"
                  suffix="$"
                />
              </v-col>
              <v-col cols="6" class="pl-1">
                <v-text-field
                  v-model.number="filters.maxPrice"
                  label="Max"
                  type="number"
                  variant="outlined"
                  density="compact"
                  hide-details
                  placeholder="Max"
                  suffix="$"
                />
              </v-col>
            </v-row>

            <!-- Available Date Range -->
            <div class="text-subtitle-2 text-medium-emphasis mb-2">
              Available Date
            </div>
            <v-row no-gutters>
              <v-col cols="12" class="mb-2">
                <v-text-field
                  v-model="filters.availableFrom"
                  label="From"
                  type="date"
                  variant="outlined"
                  density="compact"
                  hide-details
                />
              </v-col>
              <v-col cols="12">
                <v-text-field
                  v-model="filters.availableTo"
                  label="To"
                  type="date"
                  variant="outlined"
                  density="compact"
                  hide-details
                />
              </v-col>
            </v-row>
          </v-card-text>

          <v-divider></v-divider>

          <v-card-actions class="px-4 py-3">
            <v-spacer></v-spacer>
            <div class="text-caption text-medium-emphasis">
              {{ unitStore.filteredUnits.length }} units found
            </div>
          </v-card-actions>
        </v-card>
      </v-col>

      <!-- Main Content -->
      <v-col cols="12" md="9" class="pl-md-2">
        <v-card class="h-100 d-flex flex-column" :elevation="2">
          <!-- Toolbar -->
          <v-toolbar density="compact" color="transparent">
            <v-toolbar-title>Available Units</v-toolbar-title>
            <v-spacer></v-spacer>
            <v-btn
              color="primary"
              variant="outlined"
              size="small"
              class="mr-2"
              :loading="unitStore.loading"
              @click="unitStore.fetchUnits"
            >
              <v-icon start>mdi-refresh</v-icon>
              Refresh
            </v-btn>
            <v-btn
              color="primary"
              size="small"
              :disabled="unitStore.units.length === 0"
            >
              <v-icon start>mdi-download</v-icon>
              Export
            </v-btn>
          </v-toolbar>

          <v-divider></v-divider>

          <!-- Data Table -->
          <div class="flex-grow-1 overflow-auto">
            <v-data-table
              :headers="headers"
              :items="unitStore.sortedUnits"
              :loading="unitStore.loading"
              :items-per-page="20"
              :page.sync="page"
              :items-per-page-options="[10, 20, 50, 100]"
              class="elevation-0"
              hover
              fixed-header
              height="100%"
              @update:sort-by="handleSort"
            >
              <!-- Loading State -->
              <template v-slot:loading>
                <v-row justify="center" align="center" class="fill-height">
                  <v-col cols="12" class="text-center">
                    <v-progress-circular
                      indeterminate
                      color="primary"
                      size="64"
                    ></v-progress-circular>
                    <div class="mt-4 text-body-1">Loading units...</div>
                  </v-col>
                </v-row>
              </template>

              <!-- No Data State -->
              <template v-slot:no-data>
                <div class="py-8 text-center">
                  <v-icon size="48" color="grey lighten-1" class="mb-2"
                    >mdi-home-search</v-icon
                  >
                  <div class="text-h6">No units found</div>
                  <div class="text-body-2 text-medium-emphasis">
                    Try adjusting your filters or refresh the data
                  </div>
                </div>
              </template>

              <!-- Custom Cell Templates -->
              <template v-slot:item.unit="{ item }">
                <div class="font-weight-medium">{{ item.unit }}</div>
                <div class="text-caption text-medium-emphasis">
                  {{ item.building }}
                </div>
              </template>

              <template v-slot:item.size="{ item }">
                {{ item.size ? `${item.size} ft²` : "N/A" }}
              </template>

              <template v-slot:item.price="{ item }">
                <div v-if="item.prices.length > 0" class="d-flex flex-column">
                  <span class="font-weight-medium">
                    ${{ Number(item.prices[0].price).toLocaleString() }}
                  </span>
                  <span
                    v-if="item.prices.length > 1"
                    class="text-caption text-medium-emphasis"
                  >
                    {{ item.prices.length - 1 }} more price{{
                      item.prices.length > 2 ? "s" : ""
                    }}
                  </span>
                </div>
                <span v-else>N/A</span>
              </template>

              <template v-slot:item.available_date="{ value }">
                {{ formatDate(value) }}
              </template>

              <template v-slot:item.floorplan_type="{ value }">
                <v-chip
                  size="small"
                  :color="getFloorplanColor(value)"
                  variant="flat"
                  class="text-capitalize"
                >
                  {{ value }}
                </v-chip>
              </template>

              <template v-slot:item.actions="{ item }">
                <v-btn
                  icon
                  variant="text"
                  size="small"
                  @click="viewUnitDetails(item)"
                >
                  <v-icon>mdi-chevron-right</v-icon>
                </v-btn>
              </template>
            </v-data-table>
          </div>
        </v-card>
      </v-col>
    </v-row>

    <!-- Unit Details Dialog -->
    <v-dialog v-model="detailsDialog" max-width="800">
      <v-card v-if="selectedUnit">
        <v-toolbar color="primary" dark>
          <v-toolbar-title>
            Unit {{ selectedUnit.unit }}
            <div class="text-subtitle-2">{{ selectedUnit.building }}</div>
          </v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon @click="detailsDialog = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-toolbar>

        <v-card-text class="pa-0">
          <v-row no-gutters>
            <v-col cols="12" md="6" class="pa-4">
              <v-list density="compact" class="transparent">
                <v-list-item>
                  <template v-slot:prepend>
                    <v-icon class="me-4">mdi-floor-plan</v-icon>
                  </template>
                  <v-list-item-title>Floorplan Type</v-list-item-title>
                  <v-list-item-subtitle class="text-capitalize">
                    {{ selectedUnit.floorplan_type || "N/A" }}
                  </v-list-item-subtitle>
                </v-list-item>

                <v-list-item>
                  <template v-slot:prepend>
                    <v-icon class="me-4">mdi-ruler-square</v-icon>
                  </template>
                  <v-list-item-title>Size</v-list-item-title>
                  <v-list-item-subtitle>
                    {{ selectedUnit.size ? `${selectedUnit.size} ft²` : "N/A" }}
                  </v-list-item-subtitle>
                </v-list-item>

                <v-list-item>
                  <template v-slot:prepend>
                    <v-icon class="me-4">mdi-calendar-month</v-icon>
                  </template>
                  <v-list-item-title>Available Date</v-list-item-title>
                  <v-list-item-subtitle>
                    {{ formatDate(selectedUnit.available_date) }}
                  </v-list-item-subtitle>
                </v-list-item>

                <v-list-item v-if="selectedUnit.floorplan_link">
                  <template v-slot:prepend>
                    <v-icon class="me-4">mdi-link</v-icon>
                  </template>
                  <v-list-item-title>Floorplan</v-list-item-title>
                  <v-list-item-subtitle>
                    <a
                      :href="selectedUnit.floorplan_link"
                      target="_blank"
                      class="text-decoration-none"
                    >
                      View Floorplan
                    </a>
                  </v-list-item-subtitle>
                </v-list-item>

                <v-list-item v-if="selectedUnit.floorplan_note">
                  <template v-slot:prepend>
                    <v-icon class="me-4">mdi-note-text</v-icon>
                  </template>
                  <v-list-item-title>Notes</v-list-item-title>
                  <v-list-item-subtitle class="text-wrap">
                    {{ selectedUnit.floorplan_note }}
                  </v-list-item-subtitle>
                </v-list-item>
              </v-list>
            </v-col>

            <v-col cols="12" md="6" class="pa-4 bg-grey-lighten-4">
              <div class="text-h6 mb-4">Price History</div>
              <div v-if="selectedUnit.prices.length > 0" class="price-history">
                <apexchart
                  type="line"
                  height="300"
                  :options="chartOptions"
                  :series="priceSeries"
                ></apexchart>

                <v-divider class="my-4"></v-divider>

                <div class="price-list">
                  <div
                    v-for="(price, index) in selectedUnit.prices"
                    :key="index"
                    class="price-item"
                  >
                    <div class="d-flex justify-space-between">
                      <span class="text-body-2">{{
                        formatDate(price.date_fetched)
                      }}</span>
                      <span class="font-weight-medium"
                        >${{ Number(price.price).toLocaleString() }}</span
                      >
                    </div>
                    <v-progress-linear
                      v-if="index < selectedUnit.prices.length - 1"
                      :model-value="100"
                      color="grey lighten-2"
                      height="1"
                      class="my-1"
                    ></v-progress-linear>
                  </div>
                </div>
              </div>
              <div v-else class="text-center py-8">
                <v-icon size="48" color="grey lighten-1" class="mb-2"
                  >mdi-chart-line</v-icon
                >
                <div class="text-body-1">No price history available</div>
              </div>
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from "vue";
import { useUnitStore } from "@/stores/units";
import { format, parseISO } from "date-fns";

// Store
const unitStore = useUnitStore();

// Refs
const page = ref(1);
const detailsDialog = ref(false);
const selectedUnit = ref<UnitInfo | null>(null);

// Computed
const filters = computed({
  get: () => unitStore.filters,
  set: (value) => {
    unitStore.filters = value;
  },
});

const headers = [
  { title: "Unit", key: "unit", sortable: true },
  { title: "Floorplan", key: "floorplan_type", sortable: true },
  { title: "Size", key: "size", sortable: true, align: "end" },
  { title: "Price", key: "price", sortable: true, align: "end" },
  { title: "Available", key: "available_date", sortable: true },
  { title: "", key: "actions", sortable: false, width: "1%" },
];

const chartOptions = {
  chart: {
    type: "line",
    toolbar: {
      show: false,
    },
    zoom: {
      enabled: false,
    },
  },
  stroke: {
    curve: "smooth",
    width: 3,
  },
  xaxis: {
    type: "datetime",
    labels: {
      format: "MMM dd, yyyy",
    },
  },
  yaxis: {
    labels: {
      formatter: (value: number) => `$${value.toLocaleString()}`,
    },
  },
  tooltip: {
    x: {
      format: "MMM dd, yyyy",
    },
    y: {
      formatter: (value: number) => `$${value.toLocaleString()}`,
    },
  },
  colors: ["#1976D2"],
};

const priceSeries = computed(() => {
  if (!selectedUnit.value) return [];

  const prices = [...selectedUnit.value.prices]
    .sort(
      (a, b) =>
        new Date(a.date_fetched).getTime() - new Date(b.date_fetched).getTime()
    )
    .map((price) => ({
      x: new Date(price.date_fetched).getTime(),
      y: Number(price.price),
    }));

  return [
    {
      name: "Price",
      data: prices,
    },
  ];
});

// Methods
const formatDate = (dateString: string) => {
  if (!dateString || dateString === "1900-01-01" || dateString === "1970-01-01")
    return "Immediate";
  try {
    return format(parseISO(dateString), "MMM d, yyyy");
  } catch (e) {
    return dateString;
  }
};

const getFloorplanColor = (type: string) => {
  const colors: Record<string, string> = {
    studio: "blue-lighten-4",
    "1-bed": "green-lighten-4",
    "2-bed": "orange-lighten-4",
    "3-bed": "red-lighten-4",
    "4-bed": "purple-lighten-4",
    "5-bed": "teal-lighten-4",
    loft: "yellow-lighten-4",
    penthouse: "pink-lighten-4",
    duplex: "cyan-lighten-4",
    townhouse: "indigo-lighten-4",
  };
  return colors[type.toLowerCase()] || "grey-lighten-3";
};

const viewUnitDetails = (unit: UnitInfo) => {
  selectedUnit.value = unit;
  detailsDialog.value = true;
};

const handleSort = (event: any) => {
  if (event.length > 0) {
    unitStore.setSort(event[0].key);
  }
};

// Lifecycle
onMounted(() => {
  if (unitStore.units.length === 0) {
    unitStore.fetchUnits();
  }
});
</script>

<style scoped>
.h-100 {
  height: 100%;
}

.fill-height {
  height: 100%;
}

.price-history {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.price-list {
  flex: 1;
  overflow-y: auto;
  max-height: 300px;
  padding-right: 8px;
}

.price-item {
  margin-bottom: 8px;
}

/* Custom scrollbar for price list */
.price-list::-webkit-scrollbar {
  width: 6px;
}

.price-list::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.price-list::-webkit-scrollbar-thumb {
  background: #888;
  border-radius: 3px;
}

.price-list::-webkit-scrollbar-thumb:hover {
  background: #555;
}
</style>
