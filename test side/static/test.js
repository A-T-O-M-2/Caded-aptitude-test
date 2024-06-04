
let tabSwitchCounter = 0;
let formSubmitted = false;
let remainingTime = 5400; // 90 minutes in seconds



function updateTimer() {
    $.get('/time_remaining', function(data) {
        var remainingSeconds = parseInt(data);
        if (remainingSeconds <= 0) {
            autoSubmitForm(); // Submit the form
        }
        var minutes = Math.floor(remainingSeconds / 60);
        var seconds = remainingSeconds % 60;
        $('#timer').text(minutes + ":" + (seconds < 10 ? "0" + seconds : seconds));
    });
}

function updateTabSwitchCounter() {
    $.ajax({
        type: 'POST',
        url: '/update_tab_switch_counter',
        data: JSON.stringify({ 'tab_switch_counter': tabSwitchCounter }),
        contentType: 'application/json;charset=UTF-8',
        success: function(response) {
            console.log(response);
        },
        error: function(error) {
            console.error(error);
        }
    });
}

document.addEventListener("visibilitychange", function() {
    if (document.visibilityState === 'hidden' && !formSubmitted) {
        tabSwitchCounter=tabSwitchCounter*2+1;
        console.log("Tab switch counter incremented to: ", tabSwitchCounter);
        if (tabSwitchCounter > 0 ) {
            alert("You've switched tabs or minimized the window. Doing it again may lead to heavy penality");
            updateTimer(); // Update the remaining time display
        }
        updateTabSwitchCounter(); // Update the tab_switch_counter value in the session
    }
});

function submitForm() {
    formSubmitted = true; 
    $('form').submit();
}

// Function to check remaining time and auto-submit if it's zero


// C

$(document).ready(function() {
    function disableBack() {
        window.history.forward();
    }

    window.onload = disableBack();
    window.onpageshow = function(evt) {
        if (evt.persisted) disableBack();
    }

    function updateTimer() {
        $.get('/time_remaining', function(data) {
            var remainingSeconds = parseInt(data);
            if(remainingSeconds<=0){
                submitForm();
            }
            var minutes = Math.floor(remainingSeconds / 60);
            var seconds = remainingSeconds % 60;
            $('#timer').text(minutes + ":" + (seconds < 10 ? "0" + seconds : seconds));
        });
    }
    

    // Start timer on page load
    $.get('/start_timer', function() {
        setInterval(updateTimer, 1000);
    });

    // Resume timer on page refresh
    setInterval(updateTimer, 1000);
});

$(document).ready(function() {
    $('input[type="radio"]').change(function() {
        var clearButton = $(this).closest('.question').find('.clear-selection');
        clearButton.show();
    });

    $('.clear-selection').click(function(e) {
        e.preventDefault(); // Prevent form submission
        var questionDiv = $(this).closest('.question');
        questionDiv.find('input[type="radio"]').prop('checked', false);
        $(this).hide(); // Hide the "Clear Selection" button
    });
});


document.addEventListener('contextmenu', function(e) {
    e.preventDefault();
});

document.addEventListener('keydown', function(e) {
    if (e.key === 'PrintScreen') {
        alert('This has taken into consideration. One more attempt to take a screenshot, It will be notified to the company.');
    }
});
