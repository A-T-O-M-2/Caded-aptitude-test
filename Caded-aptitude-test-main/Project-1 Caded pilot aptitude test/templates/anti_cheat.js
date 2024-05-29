document.addEventListener("visibilitychange", function() {
    if (document.visibilityState === 'hidden') {
        // User switched tabs or minimized the window
        // Take appropriate action, such as pausing the exam or showing a warning
    } else {
        // User returned to the exam tab
        // Resume the exam or hide the warning
    }
});


var examWindow = window.open("exam.html", "_blank");

function checkFocus() {
    if (examWindow && !examWindow.closed && examWindow.document.hasFocus()) {
        setTimeout(checkFocus, 1000); // Check focus every second
    } else {
        // Focus lost, bring back focus to exam tab
        examWindow.focus();
        setTimeout(checkFocus, 1000); // Check focus again after bringing focus back
    }
}

checkFocus();
