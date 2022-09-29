console.log("Hello");

var socket = io();
var canvas = document.getElementById("mapCanvas");
var sumDy = document.getElementById("sumDy");
// canvas.width = window.innerWidth;
// canvas.height = window.innerHeight;
canvas.width = 700;
canvas.height = 700;
var ctx = canvas.getContext("2d");
ctx.translate(canvas.width / 2, canvas.height / 2);

let Dx = 0, Dy = 0, Dc = 0;
let prevPos = 0.0;
let curAngle = 0.0;
let valSumDy = 0.0;
let valSumDc = 0.0;
const xOffset = 382*0.19*0.5;
const MM_TO_PX = 0.5;
const AXLE_DIST = 210.0;

class Obstacle {
    constructor(x, y) {
        this.x = x;
        this.y = y;
        this.r = 5;
    }


    draw() {
        ctx.beginPath();
        ctx.fillStyle = "grey";
        ctx.arc(this.x, this.y, this.r, 0, Math.PI * 2);
        ctx.fill();
    };
}

var carImg = new Image();
carImg.onload = function() {
ctx.drawImage(carImg, 0, 0, 100, 100);
}
carImg.src = "../static/AC_photo_3.png";

var coordSvg = new Image();
coordSvg.onload = function() {
ctx.drawImage(coordSvg, 0, 0, 100, 100);
}
coordSvg.src = "../static/coordinates.svg";


var obstacles = [];

function drawCenter(){
    ctx.beginPath();
    ctx.fillStyle = "red";
    ctx.arc(0,0,5, 0, Math.PI * 2);
    ctx.fill();
}

function drawCoordinates(scale = 1.0){
    ctx.drawImage(coordSvg, -canvas.width*0.5*scale,-canvas.height*0.5*scale, canvas.width, canvas.height);
}

function drawCar(scale = 0.19){
    ctx.drawImage(carImg, -382*scale*0.5, -768*scale*0.5, 382*scale, 768*scale);
}

// obstacles.push(new Obstacle(0, 0));

// for (var o of obstacles) {
//     o.draw();
// }


function drawCurrentObstacles(curObs) {
    obstacles.push(new Obstacle(-curObs.left*MM_TO_PX*10 - xOffset,-20));
    obstacles.push(new Obstacle(curObs.right*MM_TO_PX*10 + xOffset,-20));
}

function updateTerrain(dx, dy, dc){
    dx = dx*MM_TO_PX;
    dy = dy*MM_TO_PX;
    for(const o of obstacles){
        let newx = (o.x+dx)*Math.cos(dc) - (o.y+dy)*Math.sin(dc);
        let newy = (o.x+dx)*Math.sin(dc) + (o.y+dy)*Math.cos(dc);
        o.x = newx;
        o.y = newy;
    }
    Dc += dc;
}

function clearPoints(){
    obstacles = [];
}



function Update() {
    ctx.clearRect(-canvas.width / 2, -canvas.height / 2, canvas.width, canvas.height);
    drawCenter();
    drawCar();
    drawCoordinates();

    for (let i = 0; i < obstacles.length; i++) {
        let o = obstacles[i];
        o.draw();
    }

    requestAnimationFrame(Update);
}
Update();




socket.on('distance', function(msg){
    if(msg!=undefined){
        drawCurrentObstacles({left:msg[4], right:msg[1]});
    }
});

socket.on('telemetry', function(msg){
    if(msg.angle!=undefined)curAngle = msg.angle;
    //turnRadius is a radius of a temporary path circle
    // R = L/tan(wheelAngle)
    // and then the angle dc would be the arc's central angle
    // dc = dy/R
    let turnRadius = AXLE_DIST/Math.tan(curAngle*Math.PI/180.0);
    console.log("Radius [mm]:" ,turnRadius)
    if(msg.pos){
        updateTerrain(0,msg.pos-prevPos,(msg.pos-prevPos)/turnRadius);
        prevPos=msg.pos;
    }

});








function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function demo() {
    for (let i = 0; i < 12; i++) {

        drawCurrentObstacles({left:30, right:80});
        await sleep(1000);
        updateTerrain(0, 20, 0);
        await sleep(1000);
        // drawCurrentObstacles({left:80, right:30});
        // await sleep(1000);
        // updateTerrain(20, 20, 0);
        // await sleep(1000);
        // drawCurrentObstacles({left:50, right:50});
        // await sleep(1000);
        // updateTerrain(0, 0, Math.PI/6);
        // await sleep(1000);
        // updateTerrain(0, 50, Math.PI/6);
        // await sleep(1000);
        updateTerrain(0, 20,0);
        await sleep(1000);
        updateTerrain(0, 20, Math.PI/6);
        await sleep(1000);
    }
    console.log('Done');
}

// demo();
// demo().then(()=>{
//     ctx.rotate(Math.PI/2);
//     demo().then(()=>{
//         ctx.rotate(Math.PI)
    
//     });

// });

