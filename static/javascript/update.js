// update.js

function updateGlazingDropdown(first_id, second_id) {
    const frame = document.getElementById(first_id).value;
    const glazingDropdown = document.getElementById(second_id);

    fetch('/get_window/' + frame)
        .then(response => response.json())
        .then(data => {
            if (frame === "ENEV"){
                glazingDropdown.innerHTML = '<option value="">ENEV wählen</option>';
            }else{
                glazingDropdown.innerHTML = '<option value="">Verglasung wählen</option>';
            }
            data.forEach(function (glazing) {
                const option = document.createElement('option');
                option.value = glazing;
                option.text = glazing;
                glazingDropdown.appendChild(option);
            });
        });
}

function updateConstructionDropdown(first,second) {
    const wall = document.getElementById(first).value;
    const construction = document.getElementById(second);

    fetch('/get_wall/' + wall)
        .then(response => response.json())
        .then(data => {
            if (wall === "ENEV Innenwand" || wall === "ENEV Außenwand"){
                construction.innerHTML = '<option value="">ENEV wählen</option>';
            }else{
                construction.innerHTML = '<option value="">Bauweise wählen</option>';
            }
            data.forEach(function (glazing) {
                const option = document.createElement('option');
                option.value = glazing;
                option.text = glazing;
                construction.appendChild(option);
            });
        });
}

function updateWallHeight(first,second, third, fourth) {
    const typed = document.getElementById(first).value;
    const set1 = document.getElementById(second);
    const set2 = document.getElementById(third);
    const set3 = document.getElementById(fourth);
    set1.value = typed;
    set2.value = typed;
    set3.value = typed;

}

function updateWallWidth(first,second, third, fourth) {
    const typed = document.getElementById(first).value;
    const set1 = document.getElementById(second);
    set1.value = typed;
}


function updateCeilingDropdown(first,second) {
    const ceiling = document.getElementById(first).value;
    const construction = document.getElementById(second);

    fetch('/get_ceiling/' + ceiling)
        .then(response => response.json())
        .then(data => {
            if (ceiling === "ENEV unbeheiztes Geschoss" || ceiling === "ENEV beheiztes Geschoss" || ceiling === "ENEV Dach"){
                construction.innerHTML = '<option value="">ENEV wählen</option>';
            }else{
                construction.innerHTML = '<option value="">Bauweise wählen</option>';
            }
            data.forEach(function (glazing) {
                const option = document.createElement('option');
                option.value = glazing;
                option.text = glazing;
                construction.appendChild(option);
            });
        });
}
function updateFloorDropdown(first,second) {
    const floor = document.getElementById(first).value;
    const construction = document.getElementById(second);

    fetch('/get_floor/' + floor)
        .then(response => response.json())
        .then(data => {
            if (floor === "ENEV unbeheiztes Geschoss" || floor === "ENEV beheiztes Geschoss"){
                construction.innerHTML = '<option value="">ENEV wählen</option>';
            }else{
                construction.innerHTML = '<option value="">Bauweise wählen</option>';
            }
            data.forEach(function (glazing) {
                const option = document.createElement('option');
                option.value = glazing;
                option.text = glazing;
                construction.appendChild(option);
            });
        });
}

function toggleFieldsetWindow(selectId, FieldSetId1, FieldSetId2, FieldSetId3) {
    const selectValue = document.getElementById(selectId).value;
    const fieldSet1 = document.getElementById(FieldSetId1);
    const fieldSet2 = document.getElementById(FieldSetId2);
    const fieldSet3 = document.getElementById(FieldSetId3);
    if (selectValue === "ENEV"){
        fieldSet1.style.display = "block";
        fieldSet2.style.display = "none";
        fieldSet3.style.display = "none";
    }
    else if (selectValue === "u_value") {
        fieldSet1.style.display = "none";
        fieldSet2.style.display = "block";
        fieldSet3.style.display = "none";
    } else {
        fieldSet1.style.display = "block";
        fieldSet2.style.display = "none";
        fieldSet3.style.display = "block";
    }
}

function toggleFieldsetWall(selectId, FieldSetId1, FieldSetId2, FieldSetId3, FieldSetId4) {
    const selectValue = document.getElementById(selectId).value;
    const fieldSet1 = document.getElementById(FieldSetId1);
    const fieldSet2 = document.getElementById(FieldSetId2);
    const fieldSet3 = document.getElementById(FieldSetId3);
    const fieldSet4 = document.getElementById(FieldSetId4);
    console.log(selectValue)
    if (selectValue === "Innenwand" || selectValue === 'ENEV Innenwand'){
        fieldSet1.style.display = "block";
        fieldSet2.style.display = "none";
        fieldSet3.style.display = "block";
        fieldSet4.style.display = "block";
    }
    else if (selectValue === "u_value") {
        fieldSet1.style.display = "none";
        fieldSet2.style.display = "block";
        fieldSet3.style.display = "none";
        fieldSet4.style.display = "none";
    } else {
        fieldSet1.style.display = "block";
        fieldSet2.style.display = "none";
        fieldSet3.style.display = "block";
        fieldSet4.style.display = "none";
    }
}


function toggleFieldsetDoor(selectId, FieldSetId) {
    const selectValue = document.getElementById(selectId).value;
    const fieldSet = document.getElementById(FieldSetId);
    console.log(selectValue);
    if (selectValue === "1" || selectValue === "2") {
        fieldSet.style.display = "block";
    } else {
        fieldSet.style.display = "none";
    }
}

function toggleFieldset(selectId, FieldSetId, TrueValue) {
    const selectValue = document.getElementById(selectId).value;
    const fieldSet = document.getElementById(FieldSetId);
    console.log(selectValue);
    if (selectValue === TrueValue) {
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


