var tempchart_object;

function devicedetector(){
    if ( navigator.userAgent.match(/Android/i) || navigator.userAgent.match(/iPhone/i)) {
        console.log("mobile device detected")
        document.getElementById("temp_container").classList.add("temp_container_mobile");
        document.getElementById("error_div").classList.add("error_div_mobile");
        for (var i=0; i<document.getElementsByClassName("temp").length; i++) {
            document.getElementsByClassName("temp")[i].classList.add("temp_mobile");
            document.getElementsByClassName("celsia")[i].classList.add("celsia_mobile");
        }
        for (var i=0; i<document.getElementsByClassName("temp_rozdil").length; i++) {
            document.getElementsByClassName("temp_rozdil")[i].classList.add("temp_rozdil_mobile");

        }
      }
    }
function reload(){
    location.reload();
}


function temparrayfnc(){
    console.log(temparray);
    console.log(typeof(temparray))

    for(i=0; i < temparray.length; i++){
        var tempcontainer = document.createElement("div");
            tempcontainer.className = "temp";
        var celsiadiv = document.createElement("div");
            celsiadiv.className = "celsia";
        var supelement = document.createElement("sup");
            supelement.id = "temprature_" + i;
            //supelement.innerHTML = temparray[i] + "°C";
        celsiadiv.appendChild(supelement);
        tempcontainer.appendChild(celsiadiv);
        document.getElementById("temp_container").appendChild(tempcontainer);
    }
    var temp_rozdil_container = document.createElement("div");
            temp_rozdil_container.className = "temp_rozdil";
        var celsiadiv = document.createElement("div");
            celsiadiv.className = "celsia";
        var supelement = document.createElement("sup");
           // supelement.innerHTML = "Rodzíl teplot: " + temp_rozdil + "°C";
        celsiadiv.appendChild(supelement);
        celsiadiv.appendChild(supelement);
        temp_rozdil_container.appendChild(celsiadiv);
        document.getElementById("temp_container").appendChild(temp_rozdil_container);

        //graf
    var tempchart = document.createElement("canvas");
        tempchart.id = "tempchart";
        tempchart.style.width = "98vw";
        document.getElementById("temp_container").appendChild(tempchart);


    var tempdata = [];
    var datalabels = [];
    for(i=0; i<tempdata.length; i++){
        datalabels.push(i.toString());
    }
    tempchart_object = new Chart("tempchart", {
        type: "line",

        data: {
            labels: datalabels,
            datasets: []
        },
        options: {
            legend: {
                display: false
            },
            tooltips: {
                enabled: false
            },
            scales: {
                yAxes: [{
                    ticks: {
                        fontColor: "white",
                        fontSize: 18,
                    }
                }],
                xAxes: {
                    display: true,
                    type: 'linear',
                    title: {
                        display: true
                    }
                },
            }
        }
    });



    var obnovitbttn = document.createElement("div");
        obnovitbttn.id = "error_div";
        obnovitbttn.style.display = "none";
        obnovitbttn.className = "error_div";
    document.getElementById("temp_container").appendChild(obnovitbttn);

    reloadData();

}
function errormessage(message){
    document.getElementById("error_div").style.display = "inline-block";
    document.getElementById("error_div").innerHTML = message;
    setTimeout(function(){
        document.getElementById("error_div").style.display = "none";
        document.getElementById("error_div").innerHTML = "";
    }, 4000);
}
function reloadData(){
    $.ajax({
        type: "GET",
        url: '/reload.html',
        success: function(result) {
            console.log(result);
            for(x=0; x<result.actual.length; x++){
                document.getElementById("temprature_" + x).innerHTML = result.actual[x];
            }
            tempchart_object.data.datasets = [];
            tempchart_object.data.labels = []
            for(i = 0; i<result.history[0].length; i++){
                tempchart_object.data.datasets.push({borderColor: "white", data: []})
            }
            for(y = 0; y<result.history.length; y++){
                tempchart_object.data.labels.push("");
                for(i = 0; i<result.history[0].length; i++){
                    tempchart_object.data.datasets[i].data.push(result.history[y][i])
                }
            }
            tempchart_object.update();
            setTimeout(function(){
                reloadData()
            }, 5000);
        },
        error: function(xhr, ajaxOptions, thrownError) {
            errormessage(thrownError);
        }
    });
}


