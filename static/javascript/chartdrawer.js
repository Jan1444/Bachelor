var currentDayIndex1 = 0
var chartData1;

function drawChart1(chartData) {
    const data = new google.visualization.DataTable();
    data.addColumn('string', 'Zeit');
    data.addColumn('number', 'Leistung [Wh]');
    data.addRows(chartData.slice(0, (1 + currentDayIndex1) * 96));
    chartData1 = chartData

    const options = {
        width: '100%',  // Setzen der Breite des Diagramms auf 800 Pixel
        height: 550,
        legend: 'none',
        backgroundColor: 'transparent',
        hAxis: {
            title: 'Zeit',
            titleTextStyle: {
                color: 'white',    // Farbe des Titels
                fontName: 'Arial', // Schriftart des Titels
                fontSize: 20,      // Schriftgröße des Titels
                bold: false,        // Fett gedruckter Titel
                italic: false      // Titel nicht kursiv
            },
            textStyle: {
                color: 'white',
                fontName: 'Arial New',
                fontSize: 16,
                bold: false,
                italic: false
            }
        },
        vAxis: {
            title: 'Leistung [W]',
            titleTextStyle: {
                color: 'white',    // Farbe des Titels
                fontName: 'Arial', // Schriftart des Titels
                fontSize: 20,      // Schriftgröße des Titels
                bold: false,        // Fett gedruckter Titel
                italic: false      // Titel nicht kursiv
            },
            textStyle: {
                color: 'white',
                fontName: 'Arial',
                fontSize: 14,
                bold: false,
                italic: false
            }
        },
    };

    const chart = new google.visualization.LineChart(document.getElementById('chart_div1'));
    chart.draw(data, options);
}

function addDay() {
    drawChart1(chartData1);
    currentDayIndex1++;
}


document.addEventListener('DOMContentLoaded', function () {
    addDay();
}, false);


function drawChart2(chartData2) {
    const data = new google.visualization.DataTable();
    data.addColumn('string', 'Zeit');
    data.addColumn('number', 'Wert');
    data.addRows(chartData2);

    const options = {
        title: 'Diagramm 2',
        hAxis: {title: 'Zeit'},
        vAxis: {title: 'Wert'},
        legend: 'none'
    };

    const chart = new google.visualization.LineChart(document.getElementById('chart_div2'));
    chart.draw(data, options);
}
