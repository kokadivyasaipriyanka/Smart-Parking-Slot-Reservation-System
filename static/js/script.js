function confirmDelete(message) {
    return window.confirm(message || "Are you sure?");
}

document.addEventListener("DOMContentLoaded", function () {
    const startInput = document.getElementById("reservation_start");
    const endInput = document.getElementById("reservation_end");

    if (startInput && endInput) {
        startInput.addEventListener("change", function () {
            if (startInput.value) {
                endInput.min = startInput.value;
            }
        });

        endInput.addEventListener("change", function () {
            if (startInput.value && endInput.value && endInput.value <= startInput.value) {
                alert("Reservation end time must be after the start time.");
                endInput.value = "";
            }
        });
    }

    const flashMessages = document.querySelectorAll(".flash-message");
    if (flashMessages.length > 0) {
        setTimeout(() => {
            flashMessages.forEach((message) => {
                message.style.transition = "opacity 0.5s ease";
                message.style.opacity = "0";
                setTimeout(() => {
                    message.remove();
                }, 500);
            });
        }, 4000);
    }
});