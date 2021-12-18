var socket = io();
// let dataOut = {mode: "manual", target_speed: 0, target_angle: 0};
let dataOut = {};
let dataOutUpdated = false;
// document.getElementById('button').addEventListener('click', buttonPressedEmit);
for(btn of document.getElementsByClassName('eventBtn')){
    btn.addEventListener('click', buttonPressedEmit);
}
for(range of document.getElementsByClassName('form-range')){
    range.addEventListener('input',function(event){
        const rangeID = event.srcElement.id;
        const valID = rangeID.replace('Range','Val');
        const varName = rangeID.replace('Range','');
        document.getElementById(valID).innerText = this.value;
        dataOut[varName]=this.value;
        dataOutUpdated = true;
    })
}
// document.getElementById('speed_slider').addEventListener('input',function(){
//     document.getElementById("target_speed_val").innerText = this.value;
//     dataOut["target_speed"]=this.value;
//     dataOutUpdated = true;
// });
// document.getElementById('angle_slider').addEventListener('input',function(){
//     document.getElementById("target_angle_val").innerText = this.value;
//     dataOut["target_angle"]=this.value;
//     dataOutUpdated = true;
// });

document.getElementById('signDetectorSwitch').addEventListener('change',function(){
    
});

function emitDataOut(){
    //emit only if dataOut is not empty and there is some new data
    if(dataOutUpdated && Object.keys(dataOut).length !== 0 || dataOut.constructor !== Object){
        socket.emit('mode',JSON.stringify(dataOut));
        dataOutUpdated = false;
        dataOut = {};
    }
}

function buttonPressedEmit(event){
    // console.log(id.srcElement.id);
    const buttonId = event.srcElement.id;
    socket.emit('buttonPressed',buttonId);
}



socket.on('connect', function() {
    socket.emit('my event', {data: 'I\'m connected!'});
    //socket.emit('check' ,{data: 'User Connected'})
});

socket.on('robot_info', function(msg){
    // console.log("HELLO, I RECEIVED TELEMETRY :D")
    console.log(msg);
    let cur_speed = msg.current_speed;
    let cur_angle = msg.angle;
    const voltage = msg.voltage;
    const mode = msg.mode;

    document.getElementById('current_speed').innerText = 'Current speed: '+ cur_speed + " mm/s";
    document.getElementById('current_angle').innerText = 'Angle: ' + cur_angle + " deg";
    document.getElementById('current_voltage').innerText = 'LiPo voltage: ' + voltage + " V";
    document.getElementById('speedPRange').value = msg.speed_p;
    if(msg.sensors){
        animateRobotView(msg.sensors)
    }
});

var intervalId = setInterval(emitDataOut, 200);


socket.on('image1', function(msg)
{  
   //console.log(image)
   const image_element=document.getElementById('image1');
   image_element.src="data:image/jpeg;base64,"+msg;
});
socket.on('image2', function(msg)
{  
   //console.log(image)
   const image_element=document.getElementById('image2');
   image_element.src="data:image/jpeg;base64,"+msg;
});
socket.on('image3', function(msg)
{  
   //console.log(image)
   const image_element=document.getElementById('image3');
   image_element.src="data:image/jpeg;base64,"+msg;
});
socket.on('image4', function(msg)
{  
   //console.log(image)
   const image_element=document.getElementById('image4');
   image_element.src="data:image/jpeg;base64,"+msg;
});

function animateRobotView(sensors_arr){
    for(let i=0; i<6;i++){
        sensor_label[i].textContent = sensors_arr[i] + ' cm';
    }

}


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
    rect = svgDoc.getElementById("rect31");
    for(let i=0; i<6; i++){
        sensor_label[i]=svgDoc.getElementById(`sensor_${i}_dist_text`);
    }
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