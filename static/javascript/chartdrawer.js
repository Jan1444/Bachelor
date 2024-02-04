//https://developers.google.com/chart?hl=de

var currentDayIndex1 = 1
var currentDayIndex2 = 1
var currentDayIndex3 = 1
var currentDayIndex4 = 1
var currentDayIndex5 = 1
var chartData1;
var chartData2;
var chartData3;
var chartData4;
var chartData5;


document.addEventListener('DOMContentLoaded', function () {
    addDay1();
    addDay3();
    addDay4();
    addDay5();
}, false);

function drawChart1(chartData) {
    const data = new google.visualization.DataTable();
    data.addColumn('string', 'Zeit');
    data.addColumn('number', 'Leistung [Wh]');


    chartData1 = chartData
    data.addRows(chartData.slice(0, currentDayIndex1 * 96));


    const options = {
        width: '100%',
        height: 575,
        legend: {
            position: 'right',
            textStyle: {
                color: 'white',
                fontSize: 15,
                fontName: 'Arial'
            }
        },
        is3D: true,
        backgroundColor: 'transparent',
        hAxis: {
            title: 'Zeit',
            titleTextStyle: {
                color: 'white',
                fontName: 'Arial',
                fontSize: 20,
                bold: false,
                italic: false
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
                color: 'white',
                fontName: 'Arial',
                fontSize: 20,
                bold: false,
                italic: false
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
        colors: ['blue', 'darkblue', 'lightblue']
    };

    const chart = new google.visualization.LineChart(document.getElementById('chart_div1'));
    chart.draw(data, options);
}

function addDay1() {
    drawChart1(chartData1);
    currentDayIndex1++;
}


function drawChart2(chartData) {
    const data = new google.visualization.DataTable();
    data.addColumn('string', 'Zeit');
    data.addColumn('number', 'Preis [ct/kWh]');
    data.addRows(chartData.slice(0, currentDayIndex2 * 96));
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
    data.addRows(chartData.slice(0, currentDayIndex3 * 96));
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
            minValue: 0,
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

    chartData4 = chartData
    data.addRows(chartData.slice(0, currentDayIndex4 * 96));

    const options = {
        width: '100%',  // Setzen der Breite des Diagramms auf 800 Pixel
        height: 575,
        legend: 'none',
        isStacked: true,
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
            title: 'Differenz Heizenergie Solarleistung\n[Wh]',
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

function drawChart5(chartData) {
    const data = new google.visualization.DataTable();

    data.addColumn('string', 'Zeit');
    data.addColumn('number', 'Akkuladestand [%]');

    chartData5 = chartData
    data.addRows(chartData.slice(0, currentDayIndex5 * 96));

    const options = {
        width: '100%',  // Setzen der Breite des Diagramms auf 800 Pixel
        height: 575,
        legend: 'none',
        isStacked: true,
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
            title: 'Akkuladestand [%]',
            minValue: 0,
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
        },
        colors: ['brown']
    };

    const chart = new google.visualization.AreaChart(document.getElementById('chart_div5'));
    chart.draw(data, options);
}

function addDay5() {
    drawChart5(chartData5);
    currentDayIndex5++;
}
