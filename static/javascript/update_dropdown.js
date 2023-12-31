// update_dropdown.js

function updateWindow1Dropdown() {
    const frame1 = document.getElementById('window1_frame').value;
    const glazingDropdown = document.getElementById('window1_glazing');

    fetch('/get_window/' + frame1)
        .then(response => response.json())
        .then(data => {
            glazingDropdown.innerHTML = '<option value="">Verglasung wählen</option>';
            data.forEach(function (glazing) {
                const option = document.createElement('option');
                option.value = glazing;
                option.text = glazing;
                glazingDropdown.appendChild(option);
            });
        });
}

function updateWall1Dropdown() {
    const wall1 = document.getElementById('wall1').value;
    const construction = document.getElementById('construction_wall1');

    fetch('/get_wall/' + wall1)
        .then(response => response.json())
        .then(data => {
            construction.innerHTML = '<option value="">Bauweise wählen</option>';
            data.forEach(function (glazing) {
                const option = document.createElement('option');
                option.value = glazing;
                option.text = glazing;
                construction.appendChild(option);
            });
        });
}

function updateWindow2Dropdown() {
    const frame2 = document.getElementById('window2_frame').value;
    const glazingDropdown = document.getElementById('window2_glazing');

    fetch('/get_window/' + frame2)
        .then(response => response.json())
        .then(data => {
            glazingDropdown.innerHTML = '<option value="">Verglasung wählen</option>';
            data.forEach(function (glazing) {
                const option = document.createElement('option');
                option.value = glazing;
                option.text = glazing;
                glazingDropdown.appendChild(option);
            });
        });
}

function updateWall2Dropdown() {
    const wall2 = document.getElementById('wall2').value;
    const construction = document.getElementById('construction_wall2');

    fetch('/get_wall/' + wall2)
        .then(response => response.json())
        .then(data => {
            construction.innerHTML = '<option value="">Bauweise wählen</option>';
            data.forEach(function (glazing) {
                const option = document.createElement('option');
                option.value = glazing;
                option.text = glazing;
                construction.appendChild(option);
            });
        });
}


function updateWindow3Dropdown() {
    const frame3 = document.getElementById('window3_frame').value;
    const glazingDropdown = document.getElementById('window3_glazing');

    fetch('/get_window/' + frame3)
        .then(response => response.json())
        .then(data => {
            glazingDropdown.innerHTML = '<option value="">Verglasung wählen</option>';
            data.forEach(function (glazing) {
                const option = document.createElement('option');
                option.value = glazing;
                option.text = glazing;
                glazingDropdown.appendChild(option);
            });
        });
}

function updateWall3Dropdown() {
    const wall3 = document.getElementById('wall3').value;
    const construction = document.getElementById('construction_wall3');

    fetch('/get_wall/' + wall3)
        .then(response => response.json())
        .then(data => {
            construction.innerHTML = '<option value="">Bauweise wählen</option>';
            data.forEach(function (glazing) {
                const option = document.createElement('option');
                option.value = glazing;
                option.text = glazing;
                construction.appendChild(option);
            });
        });
}

function updateWindow4Dropdown() {
    const frame4 = document.getElementById('window4_frame').value;
    const glazingDropdown = document.getElementById('window4_glazing');

    fetch('/get_window/' + frame4)
        .then(response => response.json())
        .then(data => {
            glazingDropdown.innerHTML = '<option value="">Verglasung wählen</option>';
            data.forEach(function (glazing) {
                const option = document.createElement('option');
                option.value = glazing;
                option.text = glazing;
                glazingDropdown.appendChild(option);
            });
        });
}

function updateWall4Dropdown() {
    const wall4 = document.getElementById('wall4').value;
    const construction = document.getElementById('construction_wall4');

    fetch('/get_wall/' + wall4)
        .then(response => response.json())
        .then(data => {
            construction.innerHTML = '<option value="">Bauweise wählen</option>';
            data.forEach(function (glazing) {
                const option = document.createElement('option');
                option.value = glazing;
                option.text = glazing;
                construction.appendChild(option);
            });
        });
}

function updateCeilingDropdown() {
    const ceiling = document.getElementById('ceiling').value;
    const construction = document.getElementById('construction_ceiling');

    fetch('/get_wall/' + ceiling)
        .then(response => response.json())
        .then(data => {
            construction.innerHTML = '<option value="">Bauweise wählen</option>';
            data.forEach(function (glazing) {
                const option = document.createElement('option');
                option.value = glazing;
                option.text = glazing;
                construction.appendChild(option);
            });
        });
}

function updateFloorDropdown() {
    const floor = document.getElementById('floor').value;
    const construction = document.getElementById('construction_floor');

    fetch('/get_wall/' + floor)
        .then(response => response.json())
        .then(data => {
            construction.innerHTML = '<option value="">Bauweise wählen</option>';
            data.forEach(function (glazing) {
                const option = document.createElement('option');
                option.value = glazing;
                option.text = glazing;
                construction.appendChild(option);
            });
        });
}