function toggleNew() {
    let box = document.getElementById("newBox");
    box.style.display = box.style.display === "none" ? "block" : "none";
}

function showFields(type) {
    document.getElementById("nameField").style.display = "block";
    document.getElementById("fileField").style.display = "none";
    document.getElementById("urlField").style.display = "none";

    if (type === "file") {
        document.getElementById("fileField").style.display = "block";
    }
    if (type === "link") {
        document.getElementById("urlField").style.display = "block";
    }
}
