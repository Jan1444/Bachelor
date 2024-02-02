//https://developers.google.com/chart?hl=de

var currentDayIndex1 = 1
var currentDayIndex2 = 0
var currentDayIndex3 = 0
var currentDayIndex4 = 0
var chartData1;
var chartData2;
var chartData3;
var chartData4;


document.addEventListener('DOMContentLoaded', function () {
    addDay1();
    addDay3();
    addDay4();
}, false);

function drawChart1(chartData) {
    const data = new google.visualization.DataTable();
    data.addColumn('string', 'Zeit');
    data.addColumn('number', 'Leistung [Wh]');
    data.addRows(chartData.slice(0, (currentDayIndex1) * 96));
    console.log(currentDayIndex1)
    chartData1 = chartData

    const options = {
        width: '100%',  // Setzen der Breite des Diagramms auf 800 Pixel
        height: 575,
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
            },
            minValue: 0
        },
        colors: ['blue']
    };

    const chart = new google.visualization.LineChart(document.getElementById('chart_div1'));
    chart.draw(data, options);
}

function addDay1() {
    drawChart1(chartData1);
    currentDayIndex1 ++;
}





function drawChart2(chartData) {
    const data = new google.visualization.DataTable();
    data.addColumn('string', 'Zeit');
    data.addColumn('number', 'Preis [ct/kWh]');
    data.addRows(chartData.slice(0, (1 + currentDayIndex2) * 96));
    chartData2 = chartData

    const options = {
        width: '100%',  // Setzen der Breite des Diagramms auf 800 Pixel
        height: 575,
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
            title: 'Preis [ct/kWh]',
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
            },
            minValue: 0
        },
        colors: ['green']
    };

    const chart = new google.visualization.LineChart(document.getElementById('chart_div2'));
    chart.draw(data, options);
}

function drawChart3(chartData) {
    const data = new google.visualization.DataTable();
    data.addColumn('string', 'Zeit');
    data.addColumn('number', 'Heizlast [Wh]');
    data.addRows(chartData.slice(0, (1 + currentDayIndex3) * 96));
    chartData3 = chartData

    const options = {
        width: '100%',  // Setzen der Breite des Diagramms auf 800 Pixel
        height: 575,
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
            title: 'Heizlast [Wh]',
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
            },
            minValue: 0,

        },
        colors: ['red']
    };

    const chart = new google.visualization.SteppedAreaChart(document.getElementById('chart_div3'));
    chart.draw(data, options);
}

function addDay3() {
    drawChart3(chartData3);
    currentDayIndex3++;
}

function drawChart4(chartData) {
    const data = new google.visualization.DataTable();
    data.addColumn('string', 'Zeit');
    data.addColumn('number', 'Differenz Heizenergie Solarleistung [Wh]');
    data.addRows(chartData.slice(0, (1 + currentDayIndex4) * 96));
    chartData4 = chartData

    const options = {
        width: '100%',  // Setzen der Breite des Diagramms auf 800 Pixel
        height: 575,
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
            title: 'Differenz Heizenergie Solarleistung [Wh]',
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
        colors: ['yellow']
    };

    const chart = new google.visualization.SteppedAreaChart(document.getElementById('chart_div4'));
    chart.draw(data, options);
}

function addDay4() {
    drawChart4(chartData4);
    currentDayIndex4++;
}
