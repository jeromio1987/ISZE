
(function(){
  if (typeof Chart === "undefined") { return; }
  var NAVY="#15233c", TERRA="#c0552d", STEEL="#4a6b82", SAGE="#6a7f6a", AMBER="#b8862b",
      LINE="#d9d2c6", INK="#3a3a38";

  Chart.defaults.font.family = "'Segoe UI',system-ui,Helvetica,Arial,sans-serif";
  Chart.defaults.font.size = 13;
  Chart.defaults.color = INK;
  Chart.defaults.animation = false;

  function eur(v){ return "\u20ac" + Math.round(v).toLocaleString("en-GB"); }

  /* ---- 1. agreement with independent sources ---- */
  new Chart(document.getElementById("chartAgree"), {
    type:"bar",
    data:{
      labels:[["Customs commodity code","(majority group of its own subheading)"],
              ["Isuzu catalogue figure","(majority group of its own figure)"]],
      datasets:[
        {label:"share of part numbers", data:[62.7,71.4], backgroundColor:NAVY, borderWidth:0, barPercentage:.62},
        {label:"share of billed euro",  data:[68.7,72.0], backgroundColor:TERRA, borderWidth:0, barPercentage:.62}
      ]
    },
    options:{
      maintainAspectRatio:false,
      indexAxis:"y",
      scales:{
        x:{min:0,max:100,ticks:{callback:function(v){return v+"%";}},grid:{color:LINE},title:{display:true,text:"agreement"}},
        y:{grid:{display:false},ticks:{autoSkip:false,font:{size:12}}}
      },
      plugins:{
        legend:{position:"bottom",labels:{boxWidth:12,boxHeight:12}},
        tooltip:{callbacks:{label:function(c){return c.dataset.label+": "+c.parsed.x.toFixed(1)+"%";}}}
      }
    }
  });

  /* ---- 2. air filtration: live identity leaf ---- */
  new Chart(document.getElementById("chartAir"), {
    type:"bar",
    data:{
      labels:[["Competitive parts >","Filters >","Air filter"]],
      datasets:[
        {label:"engine air filtration (live identity)", data:[1203146], backgroundColor:SAGE, borderWidth:0, barPercentage:.55}
      ]
    },
    options:{
      maintainAspectRatio:false,
      scales:{
        y:{beginAtZero:true,grid:{color:LINE},ticks:{callback:function(v){return "\u20ac"+(v/1000)+"k";}},
           title:{display:true,text:"billed euro, 18 months"}},
        x:{grid:{display:false},ticks:{font:{size:11.5}}}
      },
      plugins:{
        legend:{display:false},
        tooltip:{callbacks:{label:function(c){return c.dataset.label+": "+eur(c.parsed.y);}}}
      }
    }
  });

  /* ---- 3. identity grain, log scale ---- */
  new Chart(document.getElementById("chartGrain"), {
    type:"bar",
    data:{
      labels:[["Our leaves"],["Isuzu figures","(in the price list)"],["Volvo Impact","(three-digit)"],["TecDoc","generic articles"],["US standard","part terminologies"]],
      datasets:[{
        label:"distinct identity nodes",
        data:[171,297,1000,9900,40000],
        backgroundColor:[TERRA,NAVY,NAVY,STEEL,STEEL],
        borderWidth:0, barPercentage:.66
      }]
    },
    options:{
      maintainAspectRatio:false,
      scales:{
        y:{type:"logarithmic",min:100,max:60000,grid:{color:LINE},
           ticks:{callback:function(v){ return [100,1000,10000].indexOf(v)>-1 ? v.toLocaleString("en-GB") : ""; }},
           title:{display:true,text:"nodes (log scale)"}},
        x:{grid:{display:false},ticks:{font:{size:11.5}}}
      },
      plugins:{
        legend:{display:false},
        tooltip:{callbacks:{label:function(c){return c.parsed.y.toLocaleString("en-GB")+" nodes";}}}
      }
    }
  });

  /* ---- 4. leaf concentration ---- */
  var concLabels=["Exhaust pipe","Brake drum","Clutch kit","Steering gear / unit","Injector","Fuel pump","Radiator","Brake disc","Silencer / muffler","Other filter"];
  var concData=[71.9,69.0,66.5,64.4,62.2,52.7,51.4,48.5,48.2,46.4];
  new Chart(document.getElementById("chartConc"), {
    type:"bar",
    data:{
      labels:concLabels,
      datasets:[{
        label:"largest part number as share of the leaf's euro",
        data:concData,
        backgroundColor:concData.map(function(v){ return v>=60?TERRA:(v>=50?AMBER:STEEL); }),
        borderWidth:0, barPercentage:.68
      }]
    },
    options:{
      maintainAspectRatio:false,
      indexAxis:"y",
      scales:{
        x:{min:0,max:80,grid:{color:LINE},ticks:{callback:function(v){return v+"%";}},
           title:{display:true,text:"share of the leaf's billed euro held by one part number"}},
        y:{grid:{display:false}}
      },
      plugins:{
        legend:{display:false},
        tooltip:{callbacks:{label:function(c){return c.parsed.x.toFixed(1)+"% of the leaf";}}}
      }
    },
    plugins:[{
      id:"ref40",
      afterDraw:function(chart){
        var x=chart.scales.x.getPixelForValue(40), a=chart.chartArea, ctx=chart.ctx;
        ctx.save();
        ctx.strokeStyle="#15233c"; ctx.lineWidth=1.4; ctx.setLineDash([5,4]);
        ctx.beginPath(); ctx.moveTo(x,a.top); ctx.lineTo(x,a.bottom); ctx.stroke();
        ctx.restore();
      }
    }]
  });

  /* ---- 5. residual donut ---- */
  new Chart(document.getElementById("chartResidual"), {
    type:"doughnut",
    data:{
      labels:["In a named category","In an \u201cOther \u2026\u201d leaf","\u201cReview needed\u201d","No node at all"],
      datasets:[{
        data:[41490000,6045405,2355091,819772],
        backgroundColor:[NAVY,TERRA,AMBER,STEEL],
        borderColor:"#fff", borderWidth:2
      }]
    },
    options:{
      maintainAspectRatio:false,
      cutout:"56%",
      plugins:{
        legend:{position:"right",labels:{boxWidth:12,boxHeight:12,padding:14}},
        tooltip:{callbacks:{label:function(c){
          var tot=c.dataset.data.reduce(function(a,b){return a+b;},0);
          return c.label+": "+eur(c.parsed)+" ("+(100*c.parsed/tot).toFixed(1)+"%)";
        }}}
      }
    }
  });

  /* ---- 6. filters on the live file, 12-month cut ---- */
  new Chart(document.getElementById("chartAfter"), {
    type:"bar",
    data:{
      labels:["Fuel filter","Air filter","Oil filter","Other filter"],
      datasets:[
        {label:"live Filters family", data:[958932,796783,694420,668819], backgroundColor:TERRA, borderWidth:0, barPercentage:.7}
      ]
    },
    options:{
      maintainAspectRatio:false,
      scales:{
        y:{beginAtZero:true,grid:{color:LINE},ticks:{callback:function(v){return "\u20ac"+(v/1000)+"k";}},
           title:{display:true,text:"billed euro, 12 months to June 2026"}},
        x:{grid:{display:false}}
      },
      plugins:{
        legend:{display:false},
        tooltip:{callbacks:{label:function(c){return c.dataset.label+": "+eur(c.parsed.y);}}}
      }
    }
  });
})();
