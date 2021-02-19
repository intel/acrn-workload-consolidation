<template>
  <transition name="modal">  
    <div id="my-modal-{{id}}" click-outside="cancel()">
      <div class="modal-header">
        <h3 class="modal-title">{{title}}</h3>
      </div>
      <div class="modal-body">
        <div class="media">
          <video style="width:100%;height:100%;" controls autoplay ng-src="{{ videoSource }}"></video>
        </div>

        <pre>src = {{ videoSource }}</pre>
      </div>
      <div class="modal-footer">
        <button class="btn btn-primary" type="button" ng-click="ok()">OK</button>
        <button class="btn btn-warning" type="button" ng-click="cancel()">Cancel</button>
      </div>
    </div>
  </transition>
</template>

<script>

</script>

