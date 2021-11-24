document.getElementById('button').addEventListener('click', doSth);
document.getElementById('speed_slider').addEventListener('input',function(){
    document.getElementById("target_speed_val").innerText = this.value;
});
document.getElementById('angle_slider').addEventListener('input',function(){
    document.getElementById("target_angle_val").innerText = this.value;
});

function sliderUpdate(){
    console.log("Hello")
}

var socket = io();
socket.on('connect', function() {
    socket.emit('my event', {data: 'I\'m connected!'});
    //socket.emit('check' ,{data: 'User Connected'})
});

socket.on('robotInfo', function(msg){
    // console.log("HELLO, I RECEIVED TELEMETRY :D")
    let cur_speed = msg.speed;
    let cur_angle = msg.angle;
    document.getElementById('current_speed').innerText = 'Current speed: '+ cur_speed + " mm/s";
    document.getElementById('current_angle').innerText = 'Angle: ' + cur_angle + " deg";
});

// var intervalId = setInterval(function() {
//     socket.emit('get data');
//   }, 500);


socket.on('image', function(msg)
{  
   //console.log(image)
   const image_element=document.getElementById('image1');
   image_element.src="data:image/jpeg;base64,"+msg;
});

function doSth(){
    console.log('Clicked');
    let xhr = new XMLHttpRequest();

    xhr.open('POST','/process', true);

    xhr.onload = function(){
        if(this.status == 200){
            console.log(this.responseText)
        }
    }
    console.log(xhr);
    xhr.send("ELO");
}

var a = document.getElementById("alphasvg");
let sensor_label = []
let rect
// It's important to add an load event listener to the object,
// as it will load the svg doc asynchronously
a.addEventListener("load",function(){

    // get the inner DOM of alpha.svg
    var svgDoc = a.contentDocument;
    // get the inner element by id
    sensor_label[0] = svgDoc.getElementById("tspan161002");
    rect = svgDoc.getElementById("rect31");
    // add behaviour
    // delta.addEventListener("mousedown",function(){
    //         alert('hello world!')
    // }, false);
}, false);

socket.on('some_data',function(data){
    console.log('some_data received',data);
    document.getElementById('current_speed').textContent ='Current speed: '+data+ ' mm/s';
    sensor_label[0].textContent = data + ' cm';
    rect.style.fill = "green";
})