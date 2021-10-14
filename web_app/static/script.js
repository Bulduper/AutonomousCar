var slider = document.getElementById("myRange");
var output = document.getElementById("demo");
output.innerHTML = slider.value; // Display the default slider value

// Update the current slider value (each time you drag the slider handle)
slider.oninput = function() {
  output.innerHTML = this.value;
  // var socket = io();
  // socket.emit('slider',this.value);
//   $.post({
//     url: '/',
//     data: $('form').serialize(),
//     success: function(response){
//         alert(response);
//         alert(response.volume);             // works with jsonify()
//         alert(JSON.parse(response).volume); // works with json.dumps()
//         console.log(response);
//     },
//     error: function(error){
//         alert(response);
//         console.log(error);
//     }
// });
}