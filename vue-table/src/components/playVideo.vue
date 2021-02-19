<template>
    <div class="custom-actions">
      <button class="btn btn-sm" @click="itemAction('popup-model', rowData, rowIndex)"><play-circle-outline-icon class="icon-2x" fillColor="#656565"/></button>
    </div>
</template>

<script>
import PlayCircleOutlineIcon from "vue-material-design-icons/PlayCircleOutline.vue"
import {CONFIG} from "../config.js" 

export default {
    components: {
      PlayCircleOutlineIcon
    },
    props: {
      rowData: {
        type: Object,
        required: true
      },
      rowIndex: {
        type: Number
      }
    },
    methods: {
      itemAction (action, data, index) {
        console.log('custom-actions: ' + action, data.timestamp, index)
        var url = CONFIG.REST_API + "/video?cam=1&ts=" + data.timestamp;
        this.$parent.$parent.$parent.openVideo(url);
      }
    }
}
</script>

<style>
    /*.custom-actions button.ui.button {
      padding: 8px 8px;
    }
    .custom-actions button.ui.button > i.icon {
      margin: auto !important;
    }*/
.material-design-icon.icon-2x {
  height: 2em;
  width: 2em;
}
 
.material-design-icon.icon-2x > .material-design-icon__svg {
    height: 2em;
    width: 2em;
}
</style>
