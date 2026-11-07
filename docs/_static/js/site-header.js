/*
 * Behaviour for the libtmux.org top bar (site-header.html).
 *
 * Four jobs: the port and package pickers (search, arrow keys, Escape,
 * placement over the page), the Auto / Light / Dark control mapped onto
 * Furo's `body[data-theme]` and `localStorage.theme`, and publishing the
 * bar's height so the sticky sidebars start beneath it, and the same
 * external-link hint libtmux.org draws on links that leave it.
 */
(function () {
  "use strict";

  var root = document.querySelector(".site-header");
  if (!root) return;
  root.setAttribute("data-js", "");

  // External links ---------------------------------------------------------
  // The links to libtmux.org itself are internal on the main site, so they
  // carry no hint there; the hint marks the hosts that are external to it.
  root.querySelectorAll("a[href]").forEach(function (a) {
    var url;
    try {
      url = new URL(a.getAttribute("href"), document.baseURI);
    } catch (e) {
      return;
    }
    if (!/^https?:$/.test(url.protocol)) return;
    if (url.origin === location.origin || url.hostname === "libtmux.org") return;
    var hint = "View on " + url.hostname;
    var title = a.getAttribute("title");
    a.setAttribute("data-external-link", url.hostname);
    a.setAttribute("title", title ? hint + " \u2014 " + title : hint);
    a.setAttribute("aria-description", "External site: " + url.hostname);
  });

  // Bar height ------------------------------------------------------------
  function measure() {
    var h = root.getBoundingClientRect().height;
    if (h) document.documentElement.style.setProperty("--site-header-height", h + "px");
  }
  measure();
  if (window.ResizeObserver) new ResizeObserver(measure).observe(root);
  window.addEventListener("resize", measure);

  // Colour scheme ---------------------------------------------------------
  var STORAGE_KEY = "theme";
  var TO_PREF = { system: "auto", light: "light", dark: "dark" };
  var NEXT = { auto: "light", light: "dark", dark: "auto" };
  var LABEL = { auto: "Auto", light: "Light", dark: "Dark" };
  var FROM_PREF = { auto: "system", light: "light", dark: "dark" };

  function current() {
    var t = document.body.dataset.theme;
    return t === "light" || t === "dark" ? t : "auto";
  }

  function apply(pref) {
    document.body.dataset.theme = pref;
    try {
      localStorage.setItem(STORAGE_KEY, pref);
    } catch (e) {
      /* Storage blocked: the choice still applies to this page. */
    }
    sync();
  }

  function sync() {
    var pref = current();
    var next = NEXT[pref];
    root.querySelectorAll("[data-scheme-switch] input").forEach(function (input) {
      input.checked = input.value === FROM_PREF[pref];
    });
    root.querySelectorAll("[data-scheme-cycle]").forEach(function (button) {
      var text = "Colour scheme: " + LABEL[pref] + ". Switch to " + LABEL[next];
      button.setAttribute("aria-label", text);
      button.title = text;
      var icon = root.querySelector('[data-scheme-switch] [data-scheme="' + FROM_PREF[pref] + '"] svg');
      var slot = button.querySelector("[data-scheme-cycle-icon]");
      if (icon && slot) slot.replaceChildren(icon.cloneNode(true));
    });
  }

  root.querySelectorAll("[data-scheme-cycle]").forEach(function (button) {
    button.hidden = false;
    button.addEventListener("click", function () {
      apply(NEXT[current()]);
    });
  });
  root.querySelectorAll('[data-scheme-switch] input[type="radio"]').forEach(function (input) {
    input.addEventListener("change", function () {
      if (input.checked) apply(TO_PREF[input.value]);
    });
  });
  window.addEventListener("storage", function (event) {
    if (event.key !== STORAGE_KEY) return;
    var v = event.newValue;
    document.body.dataset.theme = v === "light" || v === "dark" ? v : "auto";
    sync();
  });
  sync();

  // Pickers ---------------------------------------------------------------
  root.querySelectorAll("[data-doc-picker]").forEach(function (picker) {
    var panel = picker.querySelector("[data-picker-panel]");
    var summary = picker.querySelector(":scope > summary");
    var search = picker.querySelector("[data-picker-search]");
    if (!panel || !summary) return;

    function groups() {
      return Array.prototype.slice.call(picker.querySelectorAll("[data-picker-group]"));
    }
    function options() {
      return Array.prototype.slice.call(picker.querySelectorAll("[data-picker-option]"));
    }

    picker.dataset.enhanced = "";
    // The top layer escapes scrolling containers; without it the native
    // details still work and every destination stays an ordinary link.
    var topLayer = typeof panel.showPopover === "function";
    if (topLayer) panel.setAttribute("popover", "manual");
    var searchLabel = picker.querySelector("[data-picker-search-label]");
    if (searchLabel) searchLabel.hidden = false;

    function position() {
      var rect = summary.getBoundingClientRect();
      if (
        !summary.getClientRects().length ||
        rect.bottom <= 8 ||
        rect.top >= window.innerHeight - 8
      ) {
        picker.open = false;
        if (topLayer && panel.matches(":popover-open")) panel.hidePopover();
        return;
      }
      var viewportWidth = document.documentElement.clientWidth;
      panel.style.maxWidth = Math.max(0, viewportWidth - 16) + "px";
      var width = panel.getBoundingClientRect().width;
      panel.style.left = Math.max(8, Math.min(rect.left, viewportWidth - width - 8)) + "px";
      var below = window.innerHeight - rect.bottom - 14;
      var above = rect.top - 14;
      var upward = below < 220 && above > below;
      panel.style.maxHeight =
        Math.max(0, Math.min(window.innerHeight - 16, upward ? above : below)) + "px";
      panel.style.top = upward ? "auto" : Math.max(8, rect.bottom + 6) + "px";
      panel.style.bottom = upward ? window.innerHeight - rect.top + 6 + "px" : "auto";
    }

    function filter() {
      var tokens = ((search && search.value) || "")
        .toLocaleLowerCase()
        .trim()
        .split(/\s+/)
        .filter(Boolean);
      var entries = options();
      entries.forEach(function (option) {
        var match = (option.dataset.match || "").toLocaleLowerCase();
        option.hidden = !tokens.every(function (t) {
          return match.indexOf(t) !== -1;
        });
      });
      groups().forEach(function (group) {
        group.hidden = !group.querySelector("[data-picker-option]:not([hidden])");
      });
      var count = entries.filter(function (o) {
        return !o.hidden;
      }).length;
      var empty = picker.querySelector("[data-picker-empty]");
      if (empty) empty.hidden = count > 0;
      var status = picker.querySelector("[data-picker-status]");
      if (status) status.textContent = tokens.length ? count + " matching entries" : "";
    }

    function visibleLinks() {
      var links = [];
      options().forEach(function (option) {
        if (option.hidden) return;
        if (option instanceof HTMLAnchorElement) links.push(option);
        else option.querySelectorAll("[data-picker-home]").forEach(function (a) { links.push(a); });
      });
      return links.filter(function (a) {
        return a.getClientRects().length;
      });
    }

    picker.addEventListener("toggle", function () {
      if (!picker.open) {
        if (topLayer && panel.matches(":popover-open")) panel.hidePopover();
        if (search && search.value) {
          search.value = "";
          filter();
        }
        return;
      }
      document.querySelectorAll("[data-doc-picker][open]").forEach(function (other) {
        if (other !== picker) other.open = false;
      });
      if (search) {
        search.value = "";
        filter();
      }
      if (topLayer) panel.showPopover();
      position();
      panel.scrollTop = 0;
      if (picker.open) {
        var first = search || panel.querySelector("a[aria-current]") || visibleLinks()[0];
        if (first) first.focus({ preventScroll: true });
      }
    });

    if (search) search.addEventListener("input", filter);

    picker.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && picker.open) {
        event.preventDefault();
        event.stopPropagation();
        picker.open = false;
        summary.focus({ preventScroll: true });
        return;
      }
      var links = visibleLinks();
      if (event.target === search) {
        if (event.key === "ArrowDown") {
          event.preventDefault();
          if (links[0]) links[0].focus();
        }
        if (event.key === "Enter" && search.value.trim()) {
          event.preventDefault();
          if (links[0]) links[0].click();
        }
      } else if (
        event.target instanceof HTMLAnchorElement &&
        links.indexOf(event.target) !== -1 &&
        ["ArrowDown", "ArrowUp", "Home", "End"].indexOf(event.key) !== -1
      ) {
        var index = links.indexOf(event.target);
        var next =
          event.key === "Home"
            ? 0
            : event.key === "End"
              ? links.length - 1
              : (index + (event.key === "ArrowDown" ? 1 : -1) + links.length) % links.length;
        event.preventDefault();
        links[next].focus();
      }
    });

    document.addEventListener("click", function (event) {
      if (picker.open && event.target instanceof Node && !picker.contains(event.target)) {
        picker.open = false;
      }
    });
    document.addEventListener("focusin", function (event) {
      if (picker.open && event.target instanceof Node && !picker.contains(event.target)) {
        picker.open = false;
      }
    });
    window.addEventListener("resize", function () {
      if (picker.open) position();
    });
    document.addEventListener(
      "scroll",
      function (event) {
        if (picker.open && event.target instanceof Node && !panel.contains(event.target)) {
          position();
        }
      },
      true,
    );
  });
})();
