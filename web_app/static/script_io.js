var socket = io();
// let dataOut = {mode: "manual", target_speed: 0, target_angle: 0};
let dataOut = {};
let dataOutUpdated = false;
let availableImgs = [];
var selectedImgKeys = [];
const defaultImgKeysHome = ['detection','undistorted','mask','warped_plot']
const defaultImgKeysSettings = ['mask','warped','undistorted_plot','None']


const consoleLogHome = document.getElementById('consoleLogHome');
// window.onload = function(){
//     console.log(window.location.pathname);
//     if(window.location.href=='/'){
//         dataOut["requestedImg"] = [1,2,3,4];
//     }
//     else {
//         dataOut["requestedImg"] = [5];
//     }
//     // dataOut["requestedImg"]
//     dataOutUpdated = true;
// }
// document.getElementById('button').addEventListener('click', buttonPressedEmit);
for(btn of document.getElementsByClassName('eventBtn')){
    // btn.addEventListener('click', buttonPressedEmit);
    btn.addEventListener('click', function(event){
        const btnID = event.srcElement.id;
        const varName = btnID.replace('Btn','');
        dataOut[varName] = {state:true};
        dataOutUpdated = true;
    });
}

for(btn of document.getElementsByClassName('captureBtn')){
    // btn.addEventListener('click', buttonPressedEmit);
    btn.addEventListener('click', function(event){
        const btnID = event.srcElement.id;
        const index = btnID.match(/\d+/)[0];
        const selectObj = document.getElementById(`image${index}Select`)
        if(selectObj){
            const selectedValue = selectObj.value;
            dataOut['capture'] = {imgKey:selectedValue};
            dataOutUpdated = true;
        }



        const varName = btnID.replace('Btn','');
        dataOut[varName] = {state:true};
        dataOutUpdated = true;
    });
}

document.getElementById('stopBtn').addEventListener('click',function(){
    document.getElementById('targetSpeedRange').value=0;
    document.getElementById('targetSpeedVal').innerText = 0;
});
document.getElementById('goBtn').addEventListener('click',function(){
    document.getElementById('targetSpeedRange').value=150;
    document.getElementById('targetSpeedVal').innerText = 150;
});



for(swtch of document.getElementsByClassName('form-check-input')){
    swtch.addEventListener('change', function(event){
        const swtchID = event.srcElement.id;
        const varName = swtchID.replace('Switch','');
        dataOut[varName]={state:this.checked};
        dataOutUpdated = true;
    })
    
}
function updateSelects(imageKeys){

    for(sel of document.getElementsByClassName('form-select')){
        let i=0;
        for(imgKey of imageKeys){
            let opt = document.createElement('option');
            opt.value = imgKey;
            opt.innerHTML = imgKey;
            sel.appendChild(opt);
            i++;
        }
        // sel.selectedIndex=2;
        if(window.location.pathname=='/'){
            const index = sel.id.match(/\d+/)[0];
            sel.value = defaultImgKeysHome[index-1];
        }
        if(window.location.pathname=='/settings'){
            const index = sel.id.match(/\d+/)[0];
            sel.value = defaultImgKeysSettings[index-1];
        }
        // sel.value = 2;
        sel.dispatchEvent(new Event('change'));
    }
}


for(range of document.getElementsByClassName('form-range')){
    range.addEventListener('input',function(event){
        const rangeID = event.srcElement.id;
        const valID = rangeID.replace('Range','Val');
        const varName = rangeID.replace('Range','');
        document.getElementById(valID).innerText = this.value;
        dataOut[varName]= varName=='targetTurn'?-this.value:this.value;
        dataOutUpdated = true;
    })
}

function updateRequestedImages(selectObj){
    const imgNo = selectObj.id.match(/\d+/)[0];
    //get the selected option text and add it to array
    selectedImgKeys[imgNo-1]=selectObj.options[selectObj.selectedIndex].text;
    console.log('selectedImgKeys',selectedImgKeys);
    dataOut['requestedImgs']=selectedImgKeys;
    dataOutUpdated = true;
    // const valID = rangeID.replace('Range','Val');
    // const varName = rangeID.replace('Range','');
    // document.getElementById(valID).innerText = this.value;
    // dataOut[varName]=this.value;
    //
}


for(sel of document.getElementsByClassName('form-select')){
    sel.addEventListener('change',function(event){
        updateRequestedImages(event.srcElement);
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

// document.getElementById('signDetectorSwitch').addEventListener('change',function(){
//     dataOut['signDetection']={state:this.checked};
//     dataOutUpdated = true;
// });

function emitDataOut(){
    //emit only if dataOut is not empty and there is some new data
    if(dataOutUpdated && Object.keys(dataOut).length !== 0 || dataOut.constructor !== Object){
        socket.emit('event',JSON.stringify(dataOut));
        dataOutUpdated = false;
        dataOut = {};
    }
}

function buttonPressedEmit(event){
    // console.log(id.srcElement.id);
    const buttonId = event.srcElement.id;
    socket.emit('buttonPressed',buttonId);
}

socket.on('logs',function(msg) {
    // console.log('Channel logs: ',msg);
    consoleLogHome.value = msg + '\r\n' + consoleLogHome.value;
});

socket.on('connect', function() {
    socket.emit('connection', {data: 'I\'m connected!'});
    //socket.emit('check' ,{data: 'User Connected'})
});

socket.on('robot_info', function(msg){
    // console.log("HELLO, I RECEIVED TELEMETRY :D")
    console.log(msg);
    let cur_speed = msg.current_speed;
    let cur_angle = msg.angle;
    const voltage = msg.voltage;
    const mode = msg.mode;

    if(cur_speed!=undefined)document.getElementById('current_speed').innerText = 'Current speed: '+ cur_speed + " mm/s";
    if(cur_angle!=undefined)document.getElementById('current_angle').innerText = 'Angle: ' + cur_angle + " deg";
    if(voltage!=undefined)document.getElementById('current_voltage').innerText = 'LiPo voltage: ' + voltage + " V";
    if(msg.fps!=undefined)document.getElementById('fps').innerHTML = msg.fps + ' FPS';
    if(msg.speed_p!=undefined)document.getElementById('speedPRange').value = msg.speed_p;
    if(msg.sensors!=undefined){
        animateRobotView(msg.sensors)
    }
});

var intervalId = setInterval(emitDataOut, 200);

socket.on('images',function(msg){
    // console.log('Images',msg);

    if(availableImgs.length == 0){
        updateSelects(Object.keys(msg));
    }
    availableImgs = Object.keys(msg);

    for(img of document.getElementsByClassName('img-fluid')){
        const index = img.id.match(/\d+/)[0];
        const selectObj = document.getElementById(`image${index}Select`)
        if(selectObj){
            const selectedValue = selectObj.value;
            if(selectedValue!='None'){
                img.src ="data:image/jpeg;base64,"+msg[selectedValue];
            } else {
                img.src = '/static/unavailable.jpg';
            }

        }
    }
    // const id = msg.id;
    // const desc = msg.description;
    // const blob = msg.blob;
    // for(img of document.getElementsByClassName())
});
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

socket.on('image5', function(msg)
{  
   //console.log(image)
   const image_element=document.getElementById('image5');
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