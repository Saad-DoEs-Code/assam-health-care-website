/*
 * Quotation form product picker.
 *
 * Progressive enhancement for templates/inquiries/inquiry_form.html.
 * Without JavaScript the form shows plain product rows that Django validates.
 * With JavaScript, visitors filter and search the catalogue, add products to a
 * list, and remove them. Each row is a Django formset form; rows are never
 * renumbered, so removing a row simply deletes it from the page and the
 * server ignores the missing index.
 */
(function () {
  "use strict";

  const form = document.querySelector("[data-inquiry-form]");
  const catalogue_element = document.getElementById("quote-catalogue");

  if (!form) {
    return;
  }

  // Prevent accidental double submission.
  form.addEventListener("submit", function () {
    const submit_button = form.querySelector("[data-submit-button]");
    if (submit_button) {
      // Disable after the browser has collected the form data.
      window.setTimeout(function () {
        submit_button.disabled = true;
        submit_button.textContent = "Sending…";
      }, 0);
    }
  });

  // Move focus to the error summary after a failed submission.
  const error_summary = form.querySelector("[data-error-summary]");
  if (error_summary) {
    error_summary.focus();
  }

  if (!catalogue_element) {
    return;
  }

  const catalogue = JSON.parse(catalogue_element.textContent);
  const products_by_id = new Map(catalogue.map(function (product) {
    return [product.id, product];
  }));

  const MAX_RESULTS = 30;

  const picker = form.querySelector("[data-product-picker]");
  const category_select = form.querySelector("[data-picker-category]");
  const search_input = form.querySelector("[data-picker-search]");
  const results_list = form.querySelector("[data-picker-results]");
  const status_element = form.querySelector("[data-picker-status]");
  const item_list = form.querySelector("[data-item-list]");
  const total_forms_input = form.querySelector("[data-total-forms]");
  const empty_message = form.querySelector("[data-empty-message]");
  const selected_title = form.querySelector("[data-selected-title]");
  const selected_count = form.querySelector("[data-selected-count]");
  const row_template = document.querySelector("[data-item-template]");

  picker.hidden = false;

  // --- Rows -----------------------------------------------------------

  function get_rows() {
    return Array.from(item_list.querySelectorAll("[data-item-row]"));
  }

  function rows_for_product(product_id) {
    return get_rows().filter(function (row) {
      return Number(row.dataset.productId) === product_id;
    });
  }

  function used_variant_ids(product_id) {
    return rows_for_product(product_id).map(function (row) {
      const select = row.querySelector("select[name$='-variant']");
      return select ? select.value : "";
    });
  }

  function add_remove_button(row) {
    const no_js_remove = row.querySelector("[data-no-js-remove]");
    if (no_js_remove) {
      no_js_remove.remove();
    }

    const header = row.querySelector(".quote-item__header");
    const name = row.querySelector(".quote-item__name");
    const button = document.createElement("button");
    button.type = "button";
    button.className = "button button--small button--ghost";
    button.textContent = "Remove";
    button.setAttribute("aria-label", "Remove " + (name ? name.textContent.trim() : "product"));
    button.addEventListener("click", function () {
      const label = name ? name.textContent.trim() : "Product";
      row.remove();
      refresh();
      announce(label + " removed from your request.");
      search_input.focus();
    });
    header.appendChild(button);
  }

  function create_row(product, preferred_variant_id) {
    const index = Number(total_forms_input.value);
    const html = row_template.innerHTML.replace(/__prefix__/g, String(index));
    const wrapper = document.createElement("div");
    wrapper.innerHTML = html.trim();
    const row = wrapper.firstElementChild;

    row.dataset.productId = String(product.id);
    row.querySelector("[data-item-name]").textContent = product.name;
    row.querySelector("[data-item-meta]").textContent = product.company;
    row.querySelector("[data-item-product]").value = String(product.id);

    const variant_field = row.querySelector("[data-item-variant-field]");
    const variant_select = row.querySelector("[data-item-variant]");

    if (product.variants.length) {
      product.variants.forEach(function (variant) {
        const option = document.createElement("option");
        option.value = String(variant.id);
        option.textContent = variant.name;
        variant_select.appendChild(option);
      });
      if (preferred_variant_id) {
        variant_select.value = preferred_variant_id;
      }
    } else {
      // No variants: do not show an empty selector.
      variant_field.remove();
    }

    total_forms_input.value = String(index + 1);
    item_list.appendChild(row);
    add_remove_button(row);
    return row;
  }

  function add_product(product_id) {
    const product = products_by_id.get(product_id);
    if (!product) {
      return;
    }

    const existing_rows = rows_for_product(product_id);

    if (existing_rows.length) {
      // One row per product + variant combination.
      const used = used_variant_ids(product_id);
      const free_variant = product.variants.find(function (variant) {
        return !used.includes(String(variant.id));
      });

      if (!product.variants.length || !free_variant) {
        const quantity_input = existing_rows[0].querySelector("input[name$='-quantity']");
        announce(product.name + " is already in your request. You can change its quantity below.");
        if (quantity_input) {
          quantity_input.focus();
        }
        return;
      }

      const row = create_row(product, String(free_variant.id));
      refresh();
      announce(product.name + " (" + free_variant.name + ") added as another size.");
      row.querySelector("select, input[type='number']").focus();
      return;
    }

    const row = create_row(product);
    refresh();
    announce(product.name + " added to your request.");
    const first_input = row.querySelector("select, input[type='number']");
    if (first_input) {
      first_input.focus();
    }
  }

  // --- Picker results -------------------------------------------------

  function announce(message) {
    status_element.textContent = message;
  }

  function matching_products() {
    const category = category_select.value;
    const terms = search_input.value.trim().toLowerCase().split(/\s+/).filter(Boolean);

    return catalogue.filter(function (product) {
      if (category && product.category !== category) {
        return false;
      }
      const haystack = (product.name + " " + product.company).toLowerCase();
      return terms.every(function (term) {
        return haystack.includes(term);
      });
    });
  }

  function render_results() {
    const matches = matching_products();
    results_list.innerHTML = "";

    if (!matches.length) {
      const empty = document.createElement("li");
      empty.className = "product-picker__empty";
      empty.textContent = "No products match your search. Try another term or category, or describe the product in the message field.";
      results_list.appendChild(empty);
      return;
    }

    matches.slice(0, MAX_RESULTS).forEach(function (product) {
      const item = document.createElement("li");
      item.className = "product-picker__result";

      const text = document.createElement("div");
      const name = document.createElement("strong");
      name.textContent = product.name;
      const meta = document.createElement("span");
      meta.className = "product-picker__meta";
      meta.textContent = product.company + (product.variants.length ? " · " + product.variants.length + " sizes" : "");
      text.appendChild(name);
      text.appendChild(meta);

      const already_added = rows_for_product(product.id).length > 0;
      const button = document.createElement("button");
      button.type = "button";
      button.className = "button button--small " + (already_added ? "button--secondary" : "button--primary");
      button.textContent = already_added ? (product.variants.length ? "Add another size" : "Added ✓") : "Add";
      button.setAttribute("aria-label", (already_added && !product.variants.length ? "Already added: " : "Add ") + product.name);
      button.addEventListener("click", function () {
        add_product(product.id);
      });

      item.appendChild(text);
      item.appendChild(button);
      results_list.appendChild(item);
    });

    if (matches.length > MAX_RESULTS) {
      const more = document.createElement("li");
      more.className = "product-picker__empty";
      more.textContent = "Showing " + MAX_RESULTS + " of " + matches.length + " products. Refine your search to see more.";
      results_list.appendChild(more);
    }
  }

  function refresh() {
    const count = get_rows().length;
    empty_message.hidden = count > 0;
    selected_title.hidden = count === 0;
    selected_count.textContent = String(count);
    render_results();
  }

  // --- Initialise ------------------------------------------------------

  // The blank fallback rows are only for visitors without JavaScript.
  item_list.querySelectorAll("[data-blank-row]").forEach(function (row) {
    row.remove();
  });

  get_rows().forEach(add_remove_button);

  category_select.addEventListener("change", render_results);
  search_input.addEventListener("input", render_results);
  // Enter in the search box should not submit the whole form.
  search_input.addEventListener("keydown", function (event) {
    if (event.key === "Enter") {
      event.preventDefault();
    }
  });

  refresh();
})();
