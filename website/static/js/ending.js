document.addEventListener("DOMContentLoaded", function () {
  const dialog = document.getElementById("ending");
  const gif = document.getElementById("popupgif");

  dialog.showModal();

  function loadGif() {
    gif.src = endingGifUrl;
    setTimeout(() => {
      gif.style.display = "none";
      dialog.close();

      var duration = 6 * 1000;
      var animationEnd = Date.now() + duration;
      var defaults = {
        startVelocity: 30,
        spread: 360,
        ticks: 60,
        zIndex: 0,
      };

      function randomInRange(min, max) {
        return Math.random() * (max - min) + min;
      }

      var interval = setInterval(function () {
        var timeLeft = animationEnd - Date.now();

        if (timeLeft <= 0) {
          return clearInterval(interval);
        }

        var particleCount = 50 * (timeLeft / duration);
        confetti({
          ...defaults,
          particleCount,
          origin: { x: randomInRange(0.1, 0.3), y: Math.random() - 0.2 },
        });
        confetti({
          ...defaults,
          particleCount,
          origin: { x: randomInRange(0.7, 0.9), y: Math.random() - 0.2 },
        });
      }, 250);
    }, 6000); // adjust this timeout to match the length of the second GIF
  }

  setTimeout(() => {
    loadGif();
  }, 4000); // adjust this timeout to match the length of the first GIF
});
