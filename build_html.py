import os

OUT = "dashboard"

def build_html():
    html = """<!DOCTYPE html>
<!DOCTYPE html>
<html>
<head>
<link rel="icon" type="image/png" href="favicon.png">
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
body{background:#0d1117;color:#e6edf3;font-family:Segoe UI;margin:0;padding:0}
.header{background:#fc4c02;color:#0d1117;font-size:24px;font-weight:bold;padding:15px;text-align:center}
.container{max-width:1400px;margin:auto;padding:20px}

/* Top row layout */
.top{display:grid;grid-template-columns:1fr 1fr 1fr;gap:20px;align-items:stretch}

/* Card styling */
.card{
  background:#161b22;
  padding:20px;
  border-radius:10px;
  display:flex;
  flex-direction:column; /* stack children vertically */
  position: relative;
}

/* Make canvas fill the card */
.card canvas{
  flex:1;
  width:100%;
}

/* Bottom row layout */
.bottom{margin-top:30px;display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:20px}

/* Table styling */
table{width:100%;border-collapse:collapse}
td,th{padding:8px;border-bottom:1px solid #30363d;text-align:center}

/* Calendar heatmap card */
#calendar-card{
  margin-top:30px;
  width:100%;
  max-width:100%;
  padding:20px;
  background:#161b22;
  border-radius:10px;
  display:flex;
  flex-direction:column;
  align-items:center;
  box-sizing: border-box;
}

#calendar-scale{
  display:flex;
  justify-content:center;
  align-items:center;
  gap:4px;
  width:100%;
  margin-top:10px;
  font-size:12px;
}

.scale-squares{
  display:flex;
  gap:2px;
}

.scale-squares div{
  width:18px; height:18px; border-radius:2px;
}

.card-header {
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 15px;
  text-align: center;
  color: #e6edf3;
}

/* ---- Adam-style heatmap layout ---- */
.heatmap-area {
  display: inline-grid;
  grid-template-columns: 36px max-content;
  grid-template-rows: 18px auto;
  column-gap: 8px;
  row-gap: 0;
  align-items: start;
  min-width: max-content;
}

.month-label,
.day-label {
  font-family: monospace;
  font-size: 10px;
  line-height: 10px;
}

.month-row {
  position: relative;
  grid-column: 2;
  grid-row: 1;
  height: 18px;
  width: max-content;
}

.month-label {
  position: absolute;
  top: 2px;
  color: #e6edf3;
}

.day-col {
  grid-column: 1;
  grid-row: 2;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.day-label {
  color: #e6edf3;
  text-align: right;
  width: 30px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
}

.grid {
  grid-column: 2;
  grid-row: 2;
  width: max-content;
  display: grid;
  grid-auto-flow: column;
  grid-auto-columns: 18px;
  grid-template-rows: repeat(7, 18px);
  gap: 2px;
  padding: 6px 4px 6px 6px;
  border-radius: 12px;
  background: #161b22;
}

.cell {
  width: 18px;
  height: 18px;
  border-radius: 3px;
  background: #0d1117;
  transition: box-shadow 0.15s ease, filter 0.15s ease;
  position: relative;
}

.cell.outside {
  background: transparent;
  pointer-events: none;
}

.cell:hover:not(.outside) {
  box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.95);
}

.tooltip {
  position: fixed;
  pointer-events: none;
  background: rgba(15, 23, 42, 0.9);
  border: 1px solid rgba(148, 163, 184, 0.4);
  color: #e6edf3;
  padding: 10px 12px;
  border-radius: 10px;
  font-size: 12px;
  font-family: monospace;
  white-space: pre-line;
  z-index: 10;
  opacity: 0;
  transform: translateY(-8px);
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.tooltip.visible {
  opacity: 1;
  transform: translateY(0);
}

/* NEW: credit watermark */
.credit {
  position: absolute;
  bottom: 10px;
  right: 12px;
  font-size: 11px;
  color: #8b949e;
  text-decoration: none;
}

.credit:hover {
  color: #fc4c02;
}
</style>
</head>
<body>
<div class="header" id="header">STRAVA DASHBOARD</div>
<div class="container">
<div class="top">
<div class="card" id="stats"></div>
<div class="card"><canvas id="d"></canvas></div>
<div class="card"><canvas id="r"></canvas></div>
</div>
<div class="bottom" id="tables"></div>

<!-- Calendar card -->
<div class="card" id="calendar-card">
  <div class="card-header" id="calendar-header"></div>

  <div class="heatmap-area">
    <div class="month-row" id="calendar-month-row"></div>

    <div class="day-col" id="calendar-day-col">
      <div class="day-label"></div>
      <div class="day-label">Mon</div>
      <div class="day-label"></div>
      <div class="day-label">Wed</div>
      <div class="day-label"></div>
      <div class="day-label">Fri</div>
      <div class="day-label"></div>
    </div>

    <div class="grid" id="calendar-grid"></div>
  </div>

  <div id="calendar-scale">
    <span>LESS</span>
    <div class="scale-squares">
      <div style="background:#ffebd6"></div>
      <div style="background:#ffd3a8"></div>
      <div style="background:#ffb97a"></div>
      <div style="background:#ff9f4c"></div>
      <div style="background:#ff8500"></div>
      <div style="background:#fc4c02"></div>
    </div>
    <span>MORE</span>
  </div>

  <div class="tooltip" id="calendar-tooltip"></div>

  <!-- NEW CREDIT LINK -->
  <a class="credit" href="https://github.com/aspain/git-sweaty/tree/main" target="_blank">
    Heatmap courtesy of git-sweaty (aspain)
  </a>
</div>

</div>

<script>
fetch('stats.json').then(r=>r.json()).then(data=>{

if(data.athlete){
  document.getElementById('header').innerText = 
    `STRAVA DASHBOARD: ${data.athlete.firstname} ${data.athlete.lastname}`;
}

function pace(sec){
  let m=Math.floor(sec/60),s=Math.round(sec%60);
  return m+":"+String(s).padStart(2,'0');
}
function timeFmt(sec){
  let d=Math.floor(sec/86400),h=Math.floor((sec%86400)/3600);
  return d+"d "+h+"h";
}
function hms(sec){
  let h = Math.floor(sec/3600);
  let m = Math.floor((sec%3600)/60);
  let s = Math.round(sec%60);
  return String(h).padStart(2,'0')+':'+String(m).padStart(2,'0')+':'+String(s).padStart(2,'0');
}

let s=data.summary;

stats.innerHTML=`
<table>
<tr><th colspan=2>Stats</th></tr>
<tr><td>Life Time Activities</td><td>${s.total_rides}</td></tr>
<tr><td>Life Time Distance</td><td>${s.total_distance.toFixed(1)} km</td></tr>
<tr><td>Life Time Elevation</td><td>${s.total_elevation.toFixed(0)} m</td></tr>
<tr><td colspan="2">
    ${data.elevation_brag ? `${data.elevation_brag}` : ""}
</td></tr>
<tr><td colspan="2">
    ${data.elevation_target ? `${data.elevation_target}` : ""}
</td></tr>
<tr><td>Time</td><td>${timeFmt(s.total_time)}</td></tr>
<tr><td>Pace</td><td>${pace(s.avg_pace_sec)}</td></tr>
<tr><td>${new Date().getFullYear()} Active Days</td><td>${s.active_days}</td></tr>
<tr><td>${new Date().getFullYear()} Rest Days</td><td>${s.rest_days}</td></tr>
</table>
`;

new Chart(document.getElementById('d'),{
  type:'bar',
  data:{
    labels:data.monthly.labels,
    datasets:[{data:data.monthly.distance,backgroundColor:'#fc4c02'}]
  },
  options:{
    plugins:{
      title:{display:true,text:'Distance per Month',color:'#e6edf3',font:{size:16}},
      legend:{display:false}
    },
    scales:{y:{beginAtZero:true}},
    maintainAspectRatio:false
  }
});

new Chart(document.getElementById('r'),{
  type:'bar',
  data:{
    labels:data.monthly.labels,
    datasets:[{data:data.monthly.rides,backgroundColor:'#fc4c02'}]
  },
  options:{
    plugins:{
      title:{display:true,text:'Rides per Month',color:'#e6edf3',font:{size:16}},
      legend:{display:false}
    },
    scales:{y:{beginAtZero:true}},
    maintainAspectRatio:false
  }
});

function make(title, rows){
  let html=`<table><tr><th colspan=2>${title}</th></tr>`;
  rows.forEach(r=>{
    let val;
    if(title.startsWith("Fastest")){
      val = hms(r.value);
    } else {
      val = (typeof r.value === "number") ? r.value.toFixed(1) : r.value;
    }
    html+=`<tr><td>${r.date}</td><td>${val}</td></tr>`;
  });
  html+="</table>";
  let div=document.createElement('div');
  div.className='card';
  div.innerHTML=html;
  tables.appendChild(div);
}

make("Longest (Km)",data.top_longest);
make("Climbs (m)", data.top_climbs.map(r => {
    return {
        date: r.date,
        value: `${r.gain_m} m (${r.category})`
    }
}));
data.fastest.forEach(g => make(g.label, g.rows));

const calendarHeader = document.getElementById('calendar-header');
const year = new Date().getFullYear();
calendarHeader.innerText = `${data.summary.total_rides} activities in ${year}`;

(function(){
  const grid = document.getElementById("calendar-grid");
  const monthRow = document.getElementById("calendar-month-row");
  const tooltip = document.getElementById("calendar-tooltip");

  const year = new Date().getFullYear();
  const start = new Date(year, 0, 1);
  const end = new Date(year + 1, 0, 1);

  const dayMs = 1000 * 60 * 60 * 24;
  const dailyTotals = data.daily_totals || {};
  const longest = data.max_daily_distance || 1;

  grid.innerHTML = "";
  monthRow.innerHTML = "";

  const startDay = start.getDay();
  const numDays = Math.ceil((end - start) / dayMs);

  function shade(val){
    if(val <= 0) return "#0d1117";

    const pct = val / longest;
    if(pct < 0.2) return "#ffebd6";
    if(pct < 0.4) return "#ffd3a8";
    if(pct < 0.6) return "#ffb97a";
    if(pct < 0.8) return "#ff9f4c";
    if(pct < 0.9) return "#ff8500";
    return "#fc4c02";
  }

  for(let i=0; i<startDay; i++){
    const cell = document.createElement("div");
    cell.className = "cell outside";
    grid.appendChild(cell);
  }

  for(let i=0; i<numDays; i++){
    const d = new Date(start.getTime() + i * dayMs);
    const iso = d.toISOString().slice(0,10);
    const val = dailyTotals[iso] || 0;

    const cell = document.createElement("div");
    cell.className = "cell";
    cell.style.background = shade(val);

    cell.addEventListener("mouseenter", (e) => {
      tooltip.classList.add("visible");
      tooltip.innerText = `${iso}\n${val.toFixed(1)} km`;
    });

    cell.addEventListener("mousemove", (e) => {
      tooltip.style.left = (e.clientX + 12) + "px";
      tooltip.style.top = (e.clientY + 12) + "px";
    });

    cell.addEventListener("mouseleave", () => {
      tooltip.classList.remove("visible");
    });

    grid.appendChild(cell);
  }

  const monthNames = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];

  for(let m=0; m<12; m++){
    const firstOfMonth = new Date(year, m, 1);
    const dayIndex = Math.floor((firstOfMonth - start) / dayMs);
    const cellIndex = dayIndex + startDay;
    const weekIndex = Math.floor(cellIndex / 7);

    const label = document.createElement("div");
    label.className = "month-label";
    label.style.left = (weekIndex * 20) + "px";
    label.innerText = monthNames[m];

    monthRow.appendChild(label);
  }
})();
});
</script>
</body>
</html>
"""
    with open(f"{OUT}/index.html","w") as f:
        f.write(html)

def main():
    build_html()
    print(
    "HTML built.\n"
    "Next steps:\n"
    "1. cd dashboard\n"
    "2. python -m http.server 8000\n"
    "3. Open browser and go to http://localhost:8000/index.html"
    )

if __name__=="__main__":
    main()