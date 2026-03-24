/**
 * SPA-like navigation for Sphinx/Furo docs.
 *
 * Intercepts internal link clicks and swaps only the content that changes
 * (article, sidebar nav tree, TOC drawer), preserving sidebar scroll
 * position, theme state, and avoiding full-page reloads.
 *
 * Progressive enhancement: no-op when fetch/DOMParser/pushState unavailable.
 */
(function () {
  "use strict";

  if (!window.fetch || !window.DOMParser || !window.history?.pushState) return;

  // --- Theme toggle (replicates Furo's cycleThemeOnce) ---

  function cycleTheme() {
    var current = localStorage.getItem("theme") || "auto";
    var prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    var next;
    if (current === "auto") next = prefersDark ? "light" : "dark";
    else if (current === "dark") next = prefersDark ? "auto" : "light";
    else next = prefersDark ? "dark" : "auto";
    document.body.dataset.theme = next;
    localStorage.setItem("theme", next);
  }

  // --- Copy button injection ---

  var copyBtnTemplate = null;

  function captureCopyIcon() {
    var btn = document.querySelector(".copybtn");
    if (btn) copyBtnTemplate = btn.cloneNode(true);
  }

  function addCopyButtons() {
    if (!copyBtnTemplate) captureCopyIcon();
    if (!copyBtnTemplate) return;
    var cells = document.querySelectorAll("div.highlight pre");
    cells.forEach(function (cell, i) {
      cell.id = "codecell" + i;
      var next = cell.nextElementSibling;
      if (next && next.classList.contains("copybtn")) {
        next.setAttribute("data-clipboard-target", "#codecell" + i);
      } else {
        var btn = copyBtnTemplate.cloneNode(true);
        btn.setAttribute("data-clipboard-target", "#codecell" + i);
        cell.insertAdjacentElement("afterend", btn);
      }
    });
  }

  // --- Minimal scrollspy ---

  var scrollCleanup = null;

  function initScrollSpy() {
    if (scrollCleanup) scrollCleanup();
    scrollCleanup = null;

    var links = document.querySelectorAll(".toc-tree a");
    if (!links.length) return;

    var entries = [];
    links.forEach(function (a) {
      var id = (a.getAttribute("href") || "").split("#")[1];
      var el = id && document.getElementById(id);
      var li = a.closest("li");
      if (el && li) entries.push({ el: el, li: li });
    });
    if (!entries.length) return;

    function update() {
      var offset =
        parseFloat(getComputedStyle(document.documentElement).fontSize) * 4;
      var active = null;
      for (var i = entries.length - 1; i >= 0; i--) {
        if (entries[i].el.getBoundingClientRect().top <= offset) {
          active = entries[i];
          break;
        }
      }
      entries.forEach(function (e) {
        e.li.classList.remove("scroll-current");
      });
      if (active) active.li.classList.add("scroll-current");
    }

    window.addEventListener("scroll", update, { passive: true });
    update();
    scrollCleanup = function () {
      window.removeEventListener("scroll", update);
    };
  }

  // --- Link interception ---

  function shouldIntercept(link, e) {
    if (e.defaultPrevented || e.button !== 0) return false;
    if (e.ctrlKey || e.metaKey || e.shiftKey || e.altKey) return false;
    if (link.origin !== location.origin) return false;
    if (link.target && link.target !== "_self") return false;
    if (link.hasAttribute("download")) return false;

    var path = link.pathname;
    if (!path.endsWith(".html") && !path.endsWith("/")) return false;

    var base = path.split("/").pop() || "";
    if (
      base === "search.html" ||
      base === "genindex.html" ||
      base === "py-modindex.html"
    )
      return false;

    if (link.closest("#sidebar-projects")) return false;
    if (link.pathname === location.pathname && link.hash) return false;

    return true;
  }

  // --- DOM swap ---

  function swap(doc) {
    [".article-container", ".sidebar-tree", ".toc-drawer"].forEach(
      function (sel) {
        var fresh = doc.querySelector(sel);
        var stale = document.querySelector(sel);
        if (fresh && stale) stale.replaceWith(fresh);
      },
    );
    var title = doc.querySelector("title");
    if (title) document.title = title.textContent || "";

    // Brand links and logo images live outside swapped regions.
    // Their relative hrefs/srcs go stale after cross-depth navigation.
    // Copy the correct values from the fetched document.
    [".sidebar-brand", ".header-center a"].forEach(function (sel) {
      var fresh = doc.querySelector(sel);
      if (!fresh) return;
      document.querySelectorAll(sel).forEach(function (el) {
        el.setAttribute("href", fresh.getAttribute("href"));
      });
    });
    var freshLogos = doc.querySelectorAll(".sidebar-logo");
    var staleLogos = document.querySelectorAll(".sidebar-logo");
    freshLogos.forEach(function (fresh, i) {
      if (staleLogos[i]) {
        staleLogos[i].setAttribute("src", fresh.getAttribute("src"));
      }
    });
  }

  function reinit() {
    addCopyButtons();
    initScrollSpy();
    var btn = document.querySelector(".content-icon-container .theme-toggle");
    if (btn) btn.addEventListener("click", cycleTheme);
  }

  // --- Navigation ---

  var currentCtrl = null;

  async function navigate(url, isPop) {
    if (currentCtrl) currentCtrl.abort();
    var ctrl = new AbortController();
    currentCtrl = ctrl;

    try {
      var resp = await fetch(url, { signal: ctrl.signal });
      if (!resp.ok) throw new Error(resp.status);

      var html = await resp.text();
      var doc = new DOMParser().parseFromString(html, "text/html");

      if (!doc.querySelector(".article-container"))
        throw new Error("no article");

      var applySwap = function () {
        swap(doc);

        if (!isPop) history.pushState({ spa: true }, "", url);

        if (!isPop) {
          var hash = new URL(url, location.href).hash;
          if (hash) {
            var el = document.querySelector(hash);
            if (el) el.scrollIntoView();
          } else {
            window.scrollTo(0, 0);
          }
        }

        reinit();
      };

      if (document.startViewTransition) {
        document.startViewTransition(applySwap);
      } else {
        applySwap();
      }
    } catch (err) {
      if (err.name === "AbortError") return;
      window.location.href = url;
    } finally {
      if (currentCtrl === ctrl) currentCtrl = null;
    }
  }

  // --- Events ---

  document.addEventListener("click", function (e) {
    var link = e.target.closest("a[href]");
    if (link && shouldIntercept(link, e)) {
      e.preventDefault();
      navigate(link.href, false);
    }
  });

  history.replaceState({ spa: true }, "");

  window.addEventListener("popstate", function () {
    navigate(location.href, true);
  });

  // --- Hover prefetch ---

  var prefetchTimer = null;

  document.addEventListener("mouseover", function (e) {
    var link = e.target.closest("a[href]");
    if (!link || link.origin !== location.origin) return;
    if (!link.pathname.endsWith(".html") && !link.pathname.endsWith("/"))
      return;

    clearTimeout(prefetchTimer);
    prefetchTimer = setTimeout(function () {
      fetch(link.href, { priority: "low" }).catch(function () {});
    }, 65);
  });

  document.addEventListener("mouseout", function (e) {
    if (e.target.closest("a[href]")) clearTimeout(prefetchTimer);
  });

  // --- Init ---

  // Copy buttons are injected by copybutton.js on DOMContentLoaded.
  // This defer script runs before DOMContentLoaded, so our handler
  // fires after copybutton's handler (registration order preserved).
  document.addEventListener("DOMContentLoaded", captureCopyIcon);
})();
