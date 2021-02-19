<script>
import { Scatter, mixins } from 'vue-chartjs'


export default {
  extends: Scatter,
  mixins: [ mixins.reactiveProp ],
  props:['chartData', 'options'],
  mounted () {
    this.renderScatterChart();
  },
  methods: {
    renderScatterChart: function() {
      this.renderChart(this.chartData, this.options);
    },
  }, 
}
</script>
