/*
 * Site-wide behaviour.
 *
 * Mobile navigation: without JavaScript the links are always visible. With
 * JavaScript, small screens get a Menu button that shows and hides them.
 */
(function () {
  "use strict";

  const toggle = document.querySelector("[data-nav-toggle]");
  const links = document.querySelector("[data-nav-links]");

  if (!toggle || !links) {
    return;
  }

  const small_screen = window.matchMedia("(max-width: 900px)");

  function set_open(is_open) {
    toggle.setAttribute("aria-expanded", String(is_open));
    links.classList.toggle("is-open", is_open);
  }

  function sync_with_screen() {
    toggle.hidden = !small_screen.matches;
    document.documentElement.classList.toggle("has-nav-toggle", small_screen.matches);
    set_open(false);
  }

  toggle.addEventListener("click", function () {
    set_open(toggle.getAttribute("aria-expanded") !== "true");
  });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && links.classList.contains("is-open")) {
      set_open(false);
      toggle.focus();
    }
  });

  small_screen.addEventListener("change", sync_with_screen);
  sync_with_screen();
})();
