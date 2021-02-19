<template>
  <div id="app" style="backgroud:#EEEEEE;">
     <my-modal v-if="showModal" @close="showModal = false" ></my-modal>
     <b-navbar toggleable="md" type="dark" sticky class="navbar-static-top mb-3" style="background-color: #0071c5;">

       <b-navbar-toggle target="nav_collapse"></b-navbar-toggle>

       <b-navbar-brand href="https://www.intel.com" class="mb-0">
        <span class="navbar-text h2 mt-2 text-white ml-0">Intel Industrial Edge Demo</span>
       </b-navbar-brand>

       <b-collapse is-nav id="nav_collapse" class="mr-3">

       <!-- Right aligned nav items -->
       <b-navbar-nav class="ml-auto">

        <b-nav-item-dropdown text="Timezone" right class="mt-2 h4 text-white">
          <b-dropdown-item href="#">US</b-dropdown-item>
          <b-dropdown-item href="#">EU</b-dropdown-item>
          <b-dropdown-item href="#">CN</b-dropdown-item>
        </b-nav-item-dropdown>

        <b-nav-item-dropdown right text="User" class="mt-2 h4 text-white">
          <b-dropdown-item href="#">Profile</b-dropdown-item>
          <b-dropdown-item href="#">Signout</b-dropdown-item>
        </b-nav-item-dropdown>
       </b-navbar-nav>

       </b-collapse>
     </b-navbar>
     <b-card-group class="ml-3 mb-3 mr-3" >
         <b-card title="Real-time Alerts" border-variant="light"
                class="mr-2 shadow">
             <my-vuetable :tableHeight="widgetHeight-20"></my-vuetable>
         </b-card>
        <b-card title="Realtime Statistics" sub-title="last 5 hours" border-variant="light"
                class="ml-2 shadow" > 
           <my-chart v-if="loaded" :chartData="dataChart" :height="widgetHeight" :options="{responsive: true, maintainAspectRatio: false}"></my-chart>
        </b-card>
     </b-card-group>
     <b-card-group class="ml-3 mr-3">
        <b-card title="Camera Location"
                class="mr-2 shadow">
          <my-map :mapHeight="widgetHeight"></my-map>
        </b-card>
        <b-card title="Cyclic Test Report"
                class="ml-2 shadow ">
          <div class="chart-wrapper">
              <div v-if="options.scales.yAxes[0].ticks.max == 6000" v-html="chartText" class="chart-text"></div>
              <my-scatter-chart :chartData="toggleChart" :styles="myStyles" :options="options"></my-scatter-chart>
              <my-toggle @toggleChart="toggleCharts"></my-toggle>
          </div>
        </b-card>
    </b-card-group>
  </div>
</template>

<script>
import axios from 'axios'
import MyVuetable from './components/MyVuetable'
import MyChart from './components/MyChart'
import MyScatterChart from './components/MyScatterChart'
import MyToggle from './components/MyToggle'
import MyMap from './components/MyMap'
import MyModal from './components/MyModal'
import {CONFIG} from "./config.js"
import { getVideo } from './xhr.js'
//import FullscreenIcon from "vue-material-design-icons/Fullscreen.vue"
//import FullscreenExitIcon from "vue-material-design-icons/FullscreenExit.vue"

export default {
  name: 'app',
  components: {
    MyVuetable,
    MyChart,
    MyScatterChart,
    MyMap,
    MyModal,
    MyToggle,
    //FullscreenIcon,
    //FullscreenExitIcon
  },
  data() { 
    return { 
      showModal: false,
      dataChart: {},
      loaded: false,
      widgetHeight: 250,
      toggleChart: {},
      fullscreen: false,
      isDistribute: true,
      chartPeriod: 0,
      chartMin: 0,
      chartAvg: 0,
      chartMax: 0,
      options: {
        responsive: true, 
        maintainAspectRatio: false,
        elements: { point: { radius: 0 } },
        scales: {
                    xAxes: [{
                            type: 'linear',
                            position: 'bottom',
                            display: true,
                            offset: true
                    }],
                    yAxes: [{
                            display: true,
                            ticks: {
                                beginAtZero: true,
                                stepSize: 0.5,
                                max: 3
                            },
                            scaleLabel: {
                                display: true,
                                labelString: 'Percentage(%)'
                            }
                    }]
        },
      }
    } 
  },
  computed: {
    myStyles () {
      return {
        height: `${this.widgetHeight - 10}px`,
        position: 'relative'
      }
    }, 
    chartText() {
      return "Period: " + this.chartPeriod + " (s)<br>" 
              + "Min: " + this.chartMin + " (ns)<br>" 
              + "Avg: " + this.chartAvg + " (ns)<br>" 
              + "Max: " + this.chartMax + " (ns)<br>"
    }
  },
  mounted() {
    this.getChartData();
    this.streamData();
    this.setHeight();
    this.$mqtt.subscribe('cyclic_test/#')
  },
  mqtt: {
    'cyclic_test': function(val) {
      var parsedData = JSON.parse(val);
      this.parseToggleData(parsedData);
    },
  },
  methods: {
    toggleCharts(value) {
      //console.log(value);
      var newVal = false;
      if(value == 'Distribution') { newVal = true; }
      else {
        newVal = false;
      }
      if(this.isDistrubute != newVal) {
        if(newVal) {
          this.setDistributeView();
        }
        else{
          this.setHistogramView();
        }
        this.isDistribute = newVal;
      }
    },
    /*fullscreenChange() {
      this.$refs['fullscreen'].toggle();
    },*/
    toggleFullScreen () {
      this.$nextTick(() => {
        //chart.resize()
      })
    },
    openVideo(videoSrc) {
      //console.log("triggered");
      //this.videoSource = url;
      getVideo(videoSrc);
      this.showModal = true;
    },
    setHeight() {
        var currentWindowHeight = window.innerHeight;
        console.log(currentWindowHeight);
        console.log((1-0.285)*currentWindowHeight/2);
        this.widgetHeight = (1-0.285)*currentWindowHeight/2; 
    },
    streamData() {
        // LIVE PUSH EVENTS
        if (typeof (EventSource) !== "undefined") {
          var app = this;
          var eventSource = new EventSource(
            CONFIG.REST_API + "/stream");
          eventSource.addEventListener('open', function (e) {
            console.log("Opened connection to event stream!");
          }, false);

          eventSource.addEventListener('error', function (e) {
            console.log("Errored!");
          }, false);

          eventSource.addEventListener('notification', function (e) {
            //var parsedData = JSON.parse(e.data);
            //var cat = parseInt(parsedData.data)
            console.log("chart event.");
            app.getChartData();
          }, false);

          /*eventSource.addEventListener('cyclic', function (e) {
            var parsedData = JSON.parse(e.data);
            //console.log(parsedData);
            app.parseToggleData(parsedData);
          }, false);*/
        }
    },
    getChartData: function() {
      console.log(encodeURIComponent(CONFIG.TIMEZONE));
      axios.get(CONFIG.REST_API + "/api/v1/count?tz=" + encodeURIComponent(CONFIG.TIMEZONE))
        .then(response => {
          if (response.status == 200) {
            console.log(response.data);
            this.dataChart = Object.assign({});
            this.$set(this.dataChart,"labels",[]);  
            this.$set(this.dataChart,"datasets",[]);
            //var newData = {"labels": "", "datasets": []};
            this.dataChart.labels = response.data["labels"];
            for (var key in response.data["data"]) {
              if(key == 47) {
                this.dataChart.datasets.push({
                  label: "Cup Detected times",
                  data: response.data["data"][key],
                  borderColor: "#3e95cd",
                  fill: false
                });
              } else if (key == 77) {
                  this.dataChart.datasets.push({
                    label: "Cell Phone Detected times",
                    data: response.data["data"][key],
                    borderColor: "#e8c3b9",
                    fill: false
                  });
              }
            }
            this.loaded = true;
         }
        })
        .catch(e => {
          console.error(e);
        s})
    },
    setDistributeView() {
        this.options.scales.yAxes[0] = {
          display: true,
          ticks: {
                   beginAtZero: true,
                   stepSize: 0.5,
                   max: 3
                 },
          scaleLabel: {
                        display: true,
                        labelString: 'Percentage(%)'
                      }
        }
    },
    setHistogramView() {
        this.options.scales.yAxes[0] = {
          display: true,
          ticks: {
                   beginAtZero: true,
                   stepSize: 1000,
                   max: 6000
                 },
          scaleLabel: {
                        display: true,
                        labelString: 'Jitter(nsec)'
                      }
        }
    },
    parseToggleData(data) {
      //console.log(data["x"]);
      this.toggleChart = Object.assign({});
      this.$set(this.toggleChart,"datasets",[]);
      if(this.isDistribute) {
        this.toggleChart.datasets.push({
          'label': 'OS Tick Jitter Distribution (100.0s)', 
          'data': data['dis'],
          'borderColor': 'red',
          'borderWidth': 1,
          'showLine': true,
        })
      }
      else {
        this.toggleChart.datasets.push({
          'label': 'Sched Jitter Histogram (100.0s)',
          'data': data['his'],
          'borderColor': 'blue',
          'borderWidth': 1,
          'showLine': true,
        });
        this.chartPeriod = data['text']['chartPeriod'];
        this.chartMin = data['text']['chartMin'];
        this.chartMax = data['text']['chartMax'];
        this.chartAvg = data['text']['chartAvg'];

      }
    },
  } 
}
</script>

<style>
.table-condensed{
  font-size: 1.3rem;
}
.btn-intel {
  background-color: #0071c5;
}
.chart-wrapper {
  position: relative;
}
.chart-text {
  position: absolute; 
  top: 4rem; 
  right: 20rem;
  font-size: 130%
}
</style>
