// Small courtesies: Escape closes an inner page, and the ink fades in once.
(function () {
  "use strict";

  document.documentElement.classList.add("is-ready");

  var close = document.querySelector(".btn--close");
  if (close) {
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape") {
        window.location.href = close.getAttribute("href");
      }
    });
  }
})();
