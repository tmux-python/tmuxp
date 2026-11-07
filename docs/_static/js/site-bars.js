/*
 * Behaviour for the libtmux.org top bar (site-header.html).
 *
 * Six jobs: the port, package, documentation, version and language pickers (search, arrow keys, Escape,
 * placement over the page), the Auto / Light / Dark control mapped onto
 * Furo's `body[data-theme]` and `localStorage.theme`, and publishing the
 * bars' heights so the sticky sidebars start beneath them, the same
 * external-link hint libtmux.org draws on links that leave it, the status
 * badges' toggletips, and the documentation bar's compact settings and
 * navigation buttons.
 */
(function () {
  "use strict";

  var root = document.querySelector(".site-header");
  if (!root) return;
  root.setAttribute("data-js", "");

  // External links ---------------------------------------------------------
  // The links to libtmux.org itself are internal on the main site, so they
  // carry no hint there; the hint marks the hosts that are external to it.
  document.querySelectorAll(".site-header a[href], .documentation-context a[href]").forEach(function (a) {
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

  // Bar heights -------------------------------------------------------------
  var context = document.querySelector(".documentation-context");
  var rootStyle = document.documentElement.style;

  function measure() {
    var h = root.getBoundingClientRect().height;
    if (h) rootStyle.setProperty("--site-header-height", h + "px");
    if (context) {
      var c = context.getBoundingClientRect().height;
      if (c) rootStyle.setProperty("--site-context-height", c + "px");
    }
    place();
  }

  // The drawers Furo fixes to the viewport open below whatever of the two bars
  // is still on screen.
  function place() {
    var bottom = root.getBoundingClientRect().bottom;
    if (context) bottom = Math.max(bottom, context.getBoundingClientRect().bottom);
    rootStyle.setProperty("--site-drawer-top", Math.max(0, bottom) + "px");
  }

  measure();
  if (window.ResizeObserver) {
    var observer = new ResizeObserver(measure);
    observer.observe(root);
    if (context) observer.observe(context);
  }
  window.addEventListener("resize", measure);
  window.addEventListener("scroll", place, { passive: true });

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
  document.querySelectorAll("[data-doc-picker]").forEach(function (picker) {
    var panel = picker.querySelector("[data-picker-panel]");
    var summary = picker.querySelector(":scope > summary");
    var search = picker.querySelector("[data-picker-search]");
    if (!panel || !summary) return;

    function groups() {
      return Array.prototype.slice.call(picker.querySelectorAll("[data-picker-group]"));
    }
    var saved = new Map(
      groups().map(function (group) {
        return [group, group instanceof HTMLDetailsElement && group.open];
      }),
    );
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
        if (group instanceof HTMLDetailsElement) {
          group.open = tokens.length ? !group.hidden : saved.get(group) || false;
        }
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
      saved = new Map(
        groups().map(function (group) {
          return [group, group instanceof HTMLDetailsElement && group.open];
        }),
      );
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

  // Status badges -----------------------------------------------------------
  // A badge opens a small card on hover or focus and pins it on click.
  var toggletips = function () {
    return Array.prototype.slice.call(document.querySelectorAll("[data-status-toggletip]"));
  };
  var tipTimers = new WeakMap();
  var tipSkipFocus = null;
  var tipParts = function (tip) {
    return { button: tip.querySelector(":scope > button"), card: tip.querySelector(":scope > [popover]") };
  };
  var tipOf = function (node) {
    return node instanceof Element ? node.closest("[data-status-toggletip]") : null;
  };
  var tipOpen = function (tip) {
    return tipParts(tip).card.matches(":popover-open");
  };
  var tipClear = function (tip) {
    window.clearTimeout(tipTimers.get(tip));
    tipTimers.delete(tip);
  };
  var tipPlace = function (tip) {
    var p = tipParts(tip);
    var rect = p.button.getBoundingClientRect();
    var width = document.documentElement.clientWidth;
    var below = window.innerHeight - rect.bottom - 6;
    var upward = p.card.offsetHeight > below && rect.top > below;
    p.card.style.left = Math.max(8, Math.min(rect.left, width - p.card.offsetWidth - 8)) + "px";
    p.card.style.top = upward
      ? Math.max(8, rect.top - 6 - p.card.offsetHeight) + "px"
      : rect.bottom + 6 + "px";
  };
  var tipShow = function (tip) {
    tipClear(tip);
    toggletips().forEach(function (other) {
      if (other !== tip && tipOpen(other)) tipHide(other);
    });
    var p = tipParts(tip);
    if (!tipOpen(tip)) p.card.showPopover();
    p.button.setAttribute("aria-expanded", "true");
    tipPlace(tip);
  };
  var tipHide = function (tip) {
    tipClear(tip);
    delete tip.dataset.pinned;
    var p = tipParts(tip);
    if (tipOpen(tip)) p.card.hidePopover();
    p.button.setAttribute("aria-expanded", "false");
  };
  var tipLater = function (tip, ms, fn) {
    tipClear(tip);
    tipTimers.set(tip, window.setTimeout(function () { fn(tip); }, ms));
  };
  if (typeof HTMLElement.prototype.showPopover === "function" && toggletips().length) {
    var on = function (type, fn) { document.addEventListener(type, fn, true); };
    on("pointerover", function (e) {
      var tip = tipOf(e.target);
      if (tip && e.pointerType === "mouse") tipLater(tip, 500, tipShow);
    });
    on("pointerout", function (e) {
      var tip = tipOf(e.target);
      if (tip && e.pointerType === "mouse" && !tip.contains(e.relatedTarget)) {
        if (tip.dataset.pinned === undefined && !tip.matches(":focus-within")) tipLater(tip, 250, tipHide);
        else tipClear(tip);
      }
    });
    on("focusin", function (e) {
      var tip = tipOf(e.target);
      if (tip && tip !== tipSkipFocus) tipShow(tip);
    });
    on("focusout", function (e) {
      var tip = tipOf(e.target);
      if (tip && !tip.contains(e.relatedTarget) && tip.dataset.pinned === undefined && !tip.matches(":hover")) {
        tipLater(tip, 250, tipHide);
      }
    });
    on("click", function (e) {
      var tip = tipOf(e.target);
      if (tip && e.target.closest("button")) {
        e.preventDefault();
        if (tipOpen(tip) && tip.dataset.pinned !== undefined) tipHide(tip);
        else {
          tipShow(tip);
          tip.dataset.pinned = "";
        }
      }
    });
    on("pointerdown", function (e) {
      toggletips().forEach(function (tip) {
        if (tipOpen(tip) && !tip.contains(e.target)) tipHide(tip);
      });
    });
    on("keydown", function (e) {
      if (e.key !== "Escape") return;
      var open = toggletips().filter(tipOpen);
      if (!open.length) return;
      e.preventDefault();
      e.stopPropagation();
      open.forEach(function (tip) {
        var focused = tip.contains(document.activeElement);
        tipHide(tip);
        if (focused) {
          tipSkipFocus = tip;
          tipParts(tip).button.focus({ preventScroll: true });
          tipSkipFocus = null;
        }
      });
    });
    on("toggle", function (e) {
      var t = e.target;
      if (t instanceof HTMLDetailsElement && !t.open) {
        t.querySelectorAll("[data-status-toggletip]").forEach(tipHide);
      }
      var tip = tipOf(t);
      if (tip && t === tipParts(tip).card) {
        tipParts(tip).button.setAttribute("aria-expanded", String(tipOpen(tip)));
      }
    });
    window.addEventListener("resize", function () { toggletips().filter(tipOpen).forEach(tipHide); });
    window.addEventListener(
      "scroll",
      function (e) {
        var open = toggletips().filter(tipOpen);
        if (!open.some(function (tip) { return tip.contains(e.target); })) open.forEach(tipHide);
      },
      true,
    );
  }

  // Documentation bar controls ----------------------------------------------
  if (context) {
    var toggle = context.querySelector("[data-context-settings-toggle]");
    var back = context.querySelector("[data-context-settings-back]");
    var settings = context.querySelector("[data-context-settings]");
    if (toggle && back && settings) {
      var compact = window.matchMedia("(max-width: 24rem)");
      context.dataset.settingsEnhanced = "";
      toggle.hidden = back.hidden = false;
      var closePickers = function () {
        settings.querySelectorAll("[data-doc-picker][open]").forEach(function (p) { p.open = false; });
      };
      var closeSettings = function () {
        closePickers();
        delete context.dataset.settingsOpen;
        toggle.setAttribute("aria-expanded", "false");
      };
      toggle.addEventListener("click", function () {
        if (!compact.matches) return;
        context.querySelectorAll("[data-doc-picker][open]").forEach(function (p) { p.open = false; });
        context.dataset.settingsOpen = "";
        toggle.setAttribute("aria-expanded", "true");
        back.focus({ preventScroll: true });
      });
      back.addEventListener("click", function () {
        closeSettings();
        toggle.focus({ preventScroll: true });
      });
      context.addEventListener("keydown", function (event) {
        if (event.key !== "Escape" || !context.hasAttribute("data-settings-open")) return;
        event.preventDefault();
        closeSettings();
        toggle.focus({ preventScroll: true });
      });
      compact.addEventListener("change", function () {
        var focused = document.activeElement;
        var navigationOpen = context.querySelector(
          '.documentation-context-navigation > :is(button, [role="button"])[aria-expanded="true"]',
        );
        closeSettings();
        if (compact.matches && navigationOpen) {
          context.dataset.settingsOpen = "";
          toggle.setAttribute("aria-expanded", "true");
        }
        if (focused instanceof HTMLElement && context.contains(focused) && !focused.getClientRects().length) {
          var next = compact.matches ? toggle : settings.querySelector("summary");
          if (next) next.focus({ preventScroll: true });
        }
      });
    }

    // The two buttons open Furo's drawers.
    [
      ["#mobile-sidebar-toggle", "__navigation"],
      ["#mobile-toc-toggle", "__toc"],
    ].forEach(function (pair) {
      var button = context.querySelector(pair[0]);
      var box = document.getElementById(pair[1]);
      if (!button || !box) return;
      var sync = function () {
        button.setAttribute("aria-expanded", String(box.checked));
      };
      button.addEventListener("click", function () {
        box.checked = !box.checked;
        sync();
      });
      box.addEventListener("change", sync);
    });
  }
})();
