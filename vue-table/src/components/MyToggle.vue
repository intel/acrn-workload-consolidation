<template>
  <div style="text-align:center">
    <toggle-switch
    :options="myOptions"
    @change="$emit('toggleChart', $event.value)"
    />
  </div>
</template>

<script>
export default {
  name: "MyToggle",
  data() {
    return {
      myOptions: {
        layout: {
          color: 'lightgray',
          backgroundColor: 'white',
          selectedBackgroundColor: 'white',
          selectedColor: 'black',
          borderColor: 'transparent',
          //fontFamily: 'Montserrat'
        },
        size: {
          height: 3,
          width: 18,
          padding: 1,
          fontSize: 1
        },
        items: {
          preSelected: 'Distribution',
          labels: [{ name: 'Distribution' }, { name: 'Histogram' }]
        }
      }
    }
  }
}
</script>
