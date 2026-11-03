/*
 * Help assistant (templates/partials/assistant.html).
 *
 * A chat-style panel with fixed options. Each option shows the visitor's
 * choice and the matching reply, copied from a <template> in the page.
 * "Find a product" searches the public catalogue. Escape closes the panel
 * and returns focus to the chat button.
 */
(function () {
  "use strict";

  const root = document.querySelector("[data-assistant]");

  if (!root || !("content" in document.createElement("template"))) {
    return;
  }

  const toggle = root.querySelector("[data-assistant-toggle]");
  const toggle_label = root.querySelector("[data-assistant-toggle-label]");
  const icon_open = root.querySelector("[data-assistant-icon-open]");
  const icon_close = root.querySelector("[data-assistant-icon-close]");
  const panel = root.querySelector("[data-assistant-panel]");
  const close_button = root.querySelector("[data-assistant-close]");
  const log = root.querySelector("[data-assistant-log]");
  const search_form = root.querySelector("[data-assistant-search]");
  const search_input = root.querySelector("[data-assistant-query]");
  const search_button = search_form.querySelector("button[type='submit']");
  const search_url = root.dataset.searchUrl;
  const whatsapp_url = root.dataset.whatsappUrl || "";

  const MIN_QUERY_LENGTH = 2;

  // --- Opening and closing ----------------------------------------------

  function is_open() {
    return toggle.getAttribute("aria-expanded") === "true";
  }

  function set_open(open) {
    panel.hidden = !open;
    toggle.setAttribute("aria-expanded", String(open));
    toggle_label.textContent = open ? "Close help" : "Need help?";
    icon_open.toggleAttribute("hidden", open);
    icon_close.toggleAttribute("hidden", !open);
    if (open) {
      const first_option = root.querySelector("[data-assistant-option]");
      if (first_option) {
        first_option.focus();
      }
    }
  }

  // --- Messages ---------------------------------------------------------

  function bubble(kind) {
    const template = root.querySelector("[data-assistant-bubble='" + kind + "']");
    return template.content.firstElementChild.cloneNode(true);
  }

  function add_message(element) {
    log.appendChild(element);
    log.scrollTop = log.scrollHeight;
  }

  function say_visitor(text) {
    const message = bubble("visitor");
    message.textContent = text;
    add_message(message);
  }

  function say_reply(key) {
    const template = root.querySelector("[data-assistant-reply='" + key + "']");
    if (!template) {
      return null;
    }
    const message = bubble("bot");
    message.appendChild(template.content.cloneNode(true));
    add_message(message);
    return message;
  }

  // --- Product search ---------------------------------------------------

  function show_search() {
    search_form.hidden = false;
    search_input.focus();
  }

  function whatsapp_link(product_name) {
    const text = "Hello Assam Healthcare, I'd like to know more about " + product_name + ".";
    return whatsapp_url + "?text=" + encodeURIComponent(text);
  }

  function show_results(results) {
    if (!results.length) {
      say_reply("search-empty");
      return;
    }

    const message = say_reply("search-results");
    message.querySelector("[data-results-intro]").textContent =
      results.length === 1 ? "I found this product:" : "I found these products:";
    const list = message.querySelector("[data-results-list]");

    results.forEach(function (product) {
      const item = bubble("result");
      const name = item.querySelector("[data-result-name]");
      name.textContent = product.name;
      name.href = product.url;
      item.querySelector("[data-result-meta]").textContent =
        product.company + " · " + product.category;
      item.querySelector("[data-result-quote]").href = product.quote_url;

      if (whatsapp_url) {
        const ask = document.createElement("a");
        ask.className = "mt-1 ml-3 inline-block text-xs font-semibold text-teal-700 hover:underline";
        ask.href = whatsapp_link(product.name);
        ask.target = "_blank";
        ask.rel = "noopener";
        ask.textContent = "Ask on WhatsApp";
        item.appendChild(ask);
      }
      list.appendChild(item);
    });
    log.scrollTop = log.scrollHeight;
  }

  function search(query) {
    say_visitor(query);

    if (query.length < MIN_QUERY_LENGTH) {
      say_reply("search-short");
      return;
    }

    search_button.disabled = true;
    fetch(search_url + "?q=" + encodeURIComponent(query), {
      headers: { Accept: "application/json" },
      credentials: "same-origin",
    })
      .then(function (response) {
        if (!response.ok) {
          throw new Error("Search failed: " + response.status);
        }
        return response.json();
      })
      .then(function (data) {
        show_results(data.results);
      })
      .catch(function () {
        say_reply("search-error");
      })
      .finally(function () {
        search_button.disabled = false;
      });
  }

  // --- Events -----------------------------------------------------------

  root.querySelectorAll("[data-assistant-option]").forEach(function (option) {
    option.addEventListener("click", function () {
      const key = option.dataset.assistantOption;
      say_visitor(option.textContent.trim());
      say_reply(key);
      if (key === "search") {
        show_search();
      }
    });
  });

  search_form.addEventListener("submit", function (event) {
    event.preventDefault();
    const query = search_input.value.trim();
    if (query) {
      search(query);
      search_input.value = "";
    }
  });

  toggle.addEventListener("click", function () {
    set_open(!is_open());
  });

  close_button.addEventListener("click", function () {
    set_open(false);
    toggle.focus();
  });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && is_open()) {
      set_open(false);
      toggle.focus();
    }
  });

  root.hidden = false;
})();
