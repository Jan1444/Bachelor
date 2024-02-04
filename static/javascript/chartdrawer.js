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


function drawChart1(chartData) {
    const data = new google.visualization.DataTable();
    data.addColumn('string', 'Zeit');
    data.addColumn('number', 'Leistung [W]');


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
    console.log('Why?')
    if (currentDayIndex1 < 15) {
        currentDayIndex1++;
    }
    drawChart1(chartData1);
}

function removeDay1() {

    if (currentDayIndex1 > 1) {
        currentDayIndex1--;
    }
    drawChart1(chartData1);
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
    if (currentDayIndex3 < 15) {
        currentDayIndex3++;
    }
    drawChart3(chartData3);
}

function removeDay3() {

    if (currentDayIndex3 > 1) {
        currentDayIndex3--;
    }
    drawChart3(chartData3);
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
    if (currentDayIndex4 < 15) {
        currentDayIndex4++;
    }
    drawChart4(chartData4);
}

function removeDay4() {

    if (currentDayIndex4 > 1) {
        currentDayIndex4--;
    }
    drawChart4(chartData4);
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
    if (currentDayIndex5 < 15) {
        currentDayIndex5++;
    }
    drawChart5(chartData5);
}

function removeDay5() {

    if (currentDayIndex5 > 1) {
        currentDayIndex5--;
    }
    drawChart5(chartData5);
}
