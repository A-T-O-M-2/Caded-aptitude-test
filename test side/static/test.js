// Disable right-click
document.addEventListener('contextmenu', function(e) {
    e.preventDefault();
});

// Disable PrintScreen
document.addEventListener('keydown', function(e) {
    if (e.key === 'PrintScreen') {
        alert('This has been taken into consideration. One more attempt to take a screenshot, it will be notified to the company.');
    }
});

let tabSwitchCounter = 0;
        let remainingTime = 90 * 60; // Initial time in seconds
        let formSubmitted = false;
        let startTime = new Date().getTime() / 1000; // Start time in seconds
        let penaltyTime = 0; // Penalty time in seconds

        // Handle tab switch or minimize
        document.addEventListener("visibilitychange", function() {
            if (document.visibilityState === 'hidden' && !formSubmitted) {
                tabSwitchCounter++;
                if (tabSwitchCounter > 0) {
                    alert("You've switched tabs or minimized the window. Doing it again may lead to a heavy penalty");
                    penaltyTime += 5*(tabSwitchCounter-1) * 60; // Add penalty time (5 minutes)
                    remainingTime -= penaltyTime; // Deduct penalty from remaining time
                    updateTimer(); // Update timer display with penalty
                }
            }
        });

        $(document).ready(function() {
            function disableBack() {
                window.history.forward();
            }

            window.onload = disableBack();
            window.onpageshow = function(evt) {
                if (evt.persisted) disableBack();
            }

            // Timer functionality
            var timerInterval;

            function startTimer() {
                timerInterval = setInterval(updateTimer, 1000);
            }

            function updateTimer() {
                remainingTime--;
                var minutes = Math.floor(remainingTime / 60);
                var seconds = remainingTime % 60;
                var formattedTime = minutes.toString().padStart(2, '0') + ':' + seconds.toString().padStart(2, '0');
                $('#timer').text(formattedTime);

                if (remainingTime <= 0) {
                    clearInterval(timerInterval);
                    submitForm();
                }
            }

            function submitForm() {
                formSubmitted = true;
                $('form').submit();
            }

            // Calculate elapsed time and adjust remaining time
            let now = new Date().getTime() / 1000; // Current time in seconds
            let elapsed = now - startTime; // Elapsed time since page load
            remainingTime -= (elapsed+penaltyTime); // Deduct elapsed time from remaining time
            
            // If the remaining time is less than or equal to 0, submit the form
            if (remainingTime <= 0) {
                submitForm();
            } else {
                startTimer();
            }
        });