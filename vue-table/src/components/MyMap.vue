<template>
  <div style="height: 100%">
    <l-map :style="style" :zoom="zoom" :center="center">
      <l-tile-layer :url="url" :attribution="attribution"></l-tile-layer>
      <l-marker :lat-lng="marker"></l-marker>
    </l-map>
  </div>
</template>

<script>
import Vue2Leaflet from 'vue2-leaflet';
import {CONFIG} from '../config.js'

export default {
  name: "MyMap",
  components: {
    'l-map': Vue2Leaflet.LMap,
    'l-tile-layer' :Vue2Leaflet.LTileLayer,
    'l-marker': Vue2Leaflet.LMarker
  },
  data () {
    return {
      zoom:15,
      center: L.latLng(CONFIG.GEO_LAT, CONFIG.GEO_LON),
      url:'http://{s}.tile.osm.org/{z}/{x}/{y}.png',
      attribution:'&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors',
      marker: L.latLng(CONFIG.GEO_LAT, CONFIG.GEO_LON),
    }
  },
  props: ["mapHeight"],
  computed: {
    style () {
      return 'width: 100%; height:' + this.mapHeight + 'px;'
    }
  }
}
</script>

<style>
@import "~leaflet/dist/leaflet.css";
</style>
