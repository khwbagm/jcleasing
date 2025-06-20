import { defineStore } from "pinia";
import { ref, computed } from "vue";
import type {
  UnitInfo,
  FilterOptions,
  SortOptions,
  UnitStoreState,
} from "@/types/units";

export const useUnitStore = defineStore("units", () => {
  // State
  const units = ref<UnitInfo[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  const filters = ref<FilterOptions>({
    building: [],
    floorplanType: [],
    minPrice: null,
    maxPrice: null,
    availableFrom: null,
    availableTo: null,
    searchQuery: "",
  });

  const sort = ref<SortOptions>({
    key: "unit",
    order: "asc",
  });

  // Getters
  const filteredUnits = computed(() => {
    return units.value.filter((unit) => {
      // Filter by building
      if (
        filters.value.building.length > 0 &&
        !filters.value.building.includes(unit.building)
      ) {
        return false;
      }

      // Filter by floorplan type
      if (
        filters.value.floorplanType.length > 0 &&
        !filters.value.floorplanType.includes(unit.floorplan_type)
      ) {
        return false;
      }

      // Filter by price
      const currentPrice = Number(unit.prices[0]?.price) || 0;
      if (
        filters.value.minPrice !== null &&
        currentPrice < filters.value.minPrice
      ) {
        return false;
      }
      if (
        filters.value.maxPrice !== null &&
        currentPrice > filters.value.maxPrice
      ) {
        return false;
      }

      // Filter by available date
      if (
        filters.value.availableFrom &&
        unit.available_date < filters.value.availableFrom
      ) {
        return false;
      }
      if (
        filters.value.availableTo &&
        unit.available_date > filters.value.availableTo
      ) {
        return false;
      }

      // Search query
      const searchLower = filters.value.searchQuery.toLowerCase();
      if (
        searchLower &&
        !(
          unit.unit.toLowerCase().includes(searchLower) ||
          unit.building.toLowerCase().includes(searchLower) ||
          unit.floorplan_type.toLowerCase().includes(searchLower)
        )
      ) {
        return false;
      }

      return true;
    });
  });

  const sortedUnits = computed(() => {
    return [...filteredUnits.value].sort((a, b) => {
      let aValue: any = a[sort.value.key as keyof UnitInfo];
      let bValue: any = b[sort.value.key as keyof UnitInfo];

      // Handle price sorting
      if (sort.value.key === "price") {
        aValue = Number(a.prices[0]?.price) || 0;
        bValue = Number(b.prices[0]?.price) || 0;
      }

      // Handle numeric values
      if (typeof aValue === "number" && typeof bValue === "number") {
        return sort.value.order === "asc" ? aValue - bValue : bValue - aValue;
      }

      // Handle string values
      aValue = String(aValue || "").toLowerCase();
      bValue = String(bValue || "").toLowerCase();

      if (aValue < bValue) return sort.value.order === "asc" ? -1 : 1;
      if (aValue > bValue) return sort.value.order === "asc" ? 1 : -1;
      return 0;
    });
  });

  const availableBuildings = computed(() => {
    const buildings = new Set<string>();
    units.value.forEach((unit) => buildings.add(unit.building));
    return Array.from(buildings).sort();
  });

  const availableFloorplanTypes = computed(() => {
    const types = new Set<string>();
    units.value.forEach((unit) => types.add(unit.floorplan_type));
    return Array.from(types).sort();
  });

  // Actions
  async function fetchUnits() {
    loading.value = true;
    error.value = null;

    try {
      // In a real app, this would be an API call
      // For now, we'll load the data from a local JSON file
      const response = await fetch("/data/units.json");
      if (!response.ok) throw new Error("Failed to fetch units");

      const data = await response.json();

      // Handle the data structure - it's an object with property keys, we need to flatten it
      if (Array.isArray(data)) {
        units.value = data;
      } else {
        // If it's an object with keys, flatten all arrays into one
        units.value = Object.values(data).flat() as UnitInfo[];
      }
    } catch (err) {
      error.value =
        err instanceof Error ? err.message : "An unknown error occurred";
      console.error("Error fetching units:", err);
    } finally {
      loading.value = false;
    }
  }

  function setSort(key: string) {
    if (sort.value.key === key) {
      sort.value.order = sort.value.order === "asc" ? "desc" : "asc";
    } else {
      sort.value.key = key;
      sort.value.order = "asc";
    }
  }

  function resetFilters() {
    filters.value = {
      building: [],
      floorplanType: [],
      minPrice: null,
      maxPrice: null,
      availableFrom: null,
      availableTo: null,
      searchQuery: "",
    };
  }

  return {
    // State
    units,
    loading,
    error,
    filters,
    sort,

    // Getters
    filteredUnits,
    sortedUnits,
    availableBuildings,
    availableFloorplanTypes,

    // Actions
    fetchUnits,
    setSort,
    resetFilters,
  };
});
