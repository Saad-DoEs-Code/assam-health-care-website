/*
 * Site-wide behaviour.
 *
 * Mobile navigation: without JavaScript the small-screen menu is simply shown
 * below the header. With JavaScript it becomes a Menu button that opens and
 * closes the panel (Escape closes it and returns focus to the button).
 */
(function () {
  "use strict";

  const toggle = document.querySelector("[data-nav-toggle]");
  const panel = document.querySelector("[data-nav-panel]");

  if (!toggle || !panel) {
    return;
  }

  const label = toggle.querySelector("[data-nav-toggle-label]");
  const icon_open = toggle.querySelector("[data-icon-open]");
  const icon_close = toggle.querySelector("[data-icon-close]");

  function set_open(is_open) {
    toggle.setAttribute("aria-expanded", String(is_open));
    panel.hidden = !is_open;
    icon_open.toggleAttribute("hidden", is_open);
    icon_close.toggleAttribute("hidden", !is_open);
    label.textContent = is_open ? "Close menu" : "Open menu";
  }

  toggle.hidden = false;
  set_open(false);

  toggle.addEventListener("click", function () {
    set_open(toggle.getAttribute("aria-expanded") !== "true");
  });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && toggle.getAttribute("aria-expanded") === "true") {
      set_open(false);
      toggle.focus();
    }
  });

  // Close the menu if the window grows to the desktop layout.
  window.matchMedia("(min-width: 1280px)").addEventListener("change", function (event) {
    if (event.matches) {
      set_open(false);
    }
  });
})();
