<template>
  <div>
    <vuetable ref="vuetable"
      :api-url="apiUrl"
      :fields="fields"
      :per-page="5"
      pagination-path=""
      :css="css.table"
      :height="tableHeight"
      @vuetable:pagination-data="onPaginationData" 
    ></vuetable>
      <!--<vuetable-pagination-info ref="paginationInfo" :css="css.paginationInfo"></vuetable-pagination-info>-->
      <vuetable-pagination ref="pagination"
        class="pull-right"
        @vuetable-pagination:change-page="onChangePage"
        :css="css.pagination">
      </vuetable-pagination>
  </div>
</template>

<script>
import Vuetable from 'vuetable-2/src/components/Vuetable'
import VuetablePagination from 'vuetable-2/src/components/VuetablePagination'
//import VuetablePaginationInfo from 'vuetable-2/src/components/VuetablePaginationInfo'
import * as moment from 'moment';
import 'moment-timezone';
import CssConfig from './VuetableCssConfig.js'
import playVideo from './playVideo'
//import VuetablePaginationBootstrap from './VuetablePaginationBootstrap'
import {CONFIG} from '../config.js'
import Vue from 'vue'


Vue.component('custom-actions', playVideo)

export default {
  components: {
    Vuetable,
    VuetablePagination,
    //VuetablePaginationInfo    
  },
  props:{
    apiUrl: {
      default: CONFIG.REST_API + "/api/v1/alerts",
      type: String
    },
    tableHeight: {
      default: 250,
      type: Number
    }
  }, 
  data() {
    return {
      css: CssConfig,
      fields: [
        {
          name: '__sequence',   // <----
          title: '#',
          titleClass: 'text-center',
          dataClass: 'text-center'
        },
        {
          name: 'timestamp',
          title: 'Timestamp',
          callback: 'convert2UTC',
          titleClass: 'text-center',
          dataClass: 'text-center'
        },
        {
          name: 'camera_id',
          title: 'Camera ID',
          titleClass: 'text-center',
          dataClass: 'text-center'
        },
        {
          name: 'class_id',
          title: 'Detected Class',
          callback: 'getClassName',
          titleClass: 'text-center',
          dataClass: 'text-center'
        },
        {
          name: '__component:custom-actions',
          title: 'Details',
          //callback: 'getVideo',
          titleClass: 'text-center',
          dataClass: 'text-center'
        }
      ]
    }
  },
  methods: {
    test() {      
        console.log("trigger");    
    },
    /*timeConverter (UNIX_timestamp) {
      var a = new Date(UNIX_timestamp);
      var year = a.getFullYear();
      var month = a.getMonth() + 1;
      var date = a.getDate();
      var hour = (a.getHours() < 10? '0' : '') + a.getHours();
      var min = (a.getMinutes() < 10? '0' : '') + a.getMinutes();
      var sec = (a.getSeconds() < 10? '0' : '') + a.getSeconds();
      var time = year + "-" + month + "-" + date + " " + hour + ":" + min + ":" + sec ;
      return time;
    },*/
    convert2UTC(unix_timestamp) {
      return moment.tz(moment.unix(unix_timestamp/1000), CONFIG.TIMEZONE).format('YYYY-MM-DD HH:mm:ss');
    },
    getClassName (class_ids) {
      var className = [];
      var i = 0;
        for(i=0; i<class_ids.length; i++){
            if(class_ids[i] == 77) className.push("cell phone");
            if(class_ids[i] == 47) className.push("cup");
      }
      return className.join();
    },
    getVideo(timestamp) {
      //var url = CONFIG.REST_API + "/video?cam=1&ts=" + timestamp;
      return '<button type="button" class="btn btn-info btn-sm">...</button>'
      //return "<a href='" + CONFIG.REST_API + "/video?cam=1&ts=" + timestamp + "' target='_blank'>...</a>"
    },
    onPaginationData (paginationData) {
      this.$refs.pagination.setPaginationData(paginationData);
      //this.$refs.paginationInfo.setPaginationData(paginationData);
    },
    onChangePage (page) {
      this.$refs.vuetable.changePage(page)
    },
    setupStream () {
      var source = new EventSource(CONFIG.REST_API + "/stream");
      var app = this;
      source.addEventListener('notification', function(event) {
        var data = JSON.parse(event.data);
        console.log("The server says " + data.fullDocument.timestamp);
        app.$refs.vuetable.refresh();
      }, false);
      source.addEventListener('error', function(event) {
        console.error("Failed to connect to event stream. Is Redis running?");
      }, false);
    },
  },
  mounted() {
    this.setupStream();
  }
}
</script>
