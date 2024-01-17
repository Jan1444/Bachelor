// update_dropdown.js

function updateWindowDropdown(first_id, second_id) {
    const frame = document.getElementById(first_id).value;
    const glazingDropdown = document.getElementById(second_id);

    fetch('/get_window/' + frame)
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

function updateWallDropdown(first,second) {
    const wall = document.getElementById(first).value;
    const construction = document.getElementById(second);

    fetch('/get_wall/' + wall)
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



function toggleFieldset(selectId, FieldSetId) {
    const selectValue = document.getElementById(selectId).value;
    const fieldSet = document.getElementById(FieldSetId);
    if (selectValue === "1") {
        fieldSet.style.display = "block";
    } else {
        fieldSet.style.display = "none";
    }
}

function toggleFieldset2(selectId, FieldSetId) {
    const selectValue = document.getElementById(selectId).value;
    const fieldSet = document.getElementById(FieldSetId);
    if (selectValue === "Danfoss" || selectValue === "Mitsubishi") {
        fieldSet.style.display = "block";
    } else {
        fieldSet.style.display = "none";
    }
}

function toggleFieldset3(selectId, FieldSetId1, FieldSetId2,FieldSetId3,FieldSetId4) {
    const selectValue = document.getElementById(selectId).value;
    const fieldSet1 = document.getElementById(FieldSetId1);
    const fieldSet2 = document.getElementById(FieldSetId2);
    const fieldSet3 = document.getElementById(FieldSetId3);
    const fieldSet4 = document.getElementById(FieldSetId4);
    if (selectValue === "ir_remote") {
        fieldSet1.style.display = "none";
        fieldSet2.style.display = "none";
        fieldSet3.style.display = "block";
        fieldSet4.style.display = "block";
    }else if (selectValue === "cloud"){
        fieldSet1.style.display = "block";
        fieldSet2.style.display = "block";
        fieldSet3.style.display = "none";
        fieldSet4.style.display = "none";
    }
}