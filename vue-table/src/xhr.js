'use strict';

export function getVideo(url) {
  var xhr = new XMLHttpRequest();
  xhr.responseType = 'blob';

  xhr.onload = function() {
  
    var reader = new FileReader();
  
    reader.onloadend = function() {

      if (xhr.status !== 200) {
        console.error('Unexpected status code ' + xhr.status + ' for ' + url);
        return false;
      }
  
      var byteCharacters = atob(reader.result.slice(reader.result.indexOf(',') + 1));
    
      var byteNumbers = new Array(byteCharacters.length);

      for (var i = 0; i < byteCharacters.length; i++) {
      
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      
      }

      var byteArray = new Uint8Array(byteNumbers);
      var blob = new Blob([byteArray], {type: 'video/mp4'});
      var url = URL.createObjectURL(blob);
    
      document.getElementById('videoplayer').src = url;
      //this.
    }
  
    reader.readAsDataURL(xhr.response);
  
  };

  xhr.open('GET', url);
  xhr.send();
}
