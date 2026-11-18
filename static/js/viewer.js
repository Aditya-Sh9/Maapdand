/* Image viewer on the review and result pages.
   Rows and boxes share a data-field key (a field name on review, a rule code on result);
   focusing or opening a row lights up its box and switches to the image it came from. */
(function () {
  // Review values can be long (a full address): grow each box to fit instead of clipping it.
  // Browsers with CSS field-sizing do this on their own; this covers the rest.
  if (!(window.CSS && CSS.supports("field-sizing", "content"))) {
    document.querySelectorAll("textarea.autogrow").forEach(function (t) {
      var fit = function () { t.style.height = "auto"; t.style.height = t.scrollHeight + 2 + "px"; };
      t.addEventListener("input", fit);
      fit();
    });
  }

  var frames = document.querySelectorAll(".viewer__frame");
  var tabs = document.querySelectorAll(".viewer__tab");
  if (!frames.length) return;

  function showImage(index) {
    frames.forEach(function (f) { f.classList.toggle("is-active", f.dataset.index === String(index)); });
    tabs.forEach(function (t) { t.setAttribute("aria-selected", t.dataset.index === String(index) ? "true" : "false"); });
  }
  tabs.forEach(function (t) { t.addEventListener("click", function () { showImage(t.dataset.index); }); });

  function highlight(key, scroll) {
    var boxes = document.querySelectorAll('.evbox[data-field="' + key + '"]');
    document.querySelectorAll(".evbox.is-on").forEach(function (b) { b.classList.remove("is-on"); });
    if (!boxes.length) return;
    showImage(boxes[0].closest(".viewer__frame").dataset.index);
    boxes.forEach(function (b) {
      b.classList.add("is-on");
      if (Motion.ok) gsap.fromTo(b, { scale: 1.08 }, { scale: 1, duration: 0.3, ease: Motion.ease, clearProps: "transform" });
    });
    // On narrow screens the image sits above the list, so bring it into view.
    if (scroll && window.innerWidth < 960) {
      document.querySelector(".viewer").scrollIntoView({ behavior: Motion.ok ? "smooth" : "auto", block: "start" });
    }
  }

  document.querySelectorAll("[data-field]:not(.evbox)").forEach(function (row) {
    row.addEventListener("focusin", function () { highlight(row.dataset.field, false); });
    row.addEventListener("mouseenter", function () { highlight(row.dataset.field, false); });
  });
  document.querySelectorAll("details[data-field]").forEach(function (d) {
    d.addEventListener("toggle", function () { if (d.open) highlight(d.dataset.field, false); });
  });
  document.querySelectorAll("[data-show]").forEach(function (btn) {
    btn.addEventListener("click", function (e) { e.preventDefault(); highlight(btn.dataset.show, true); });
  });

  // First view: boxes draw in one after another so the eye follows where values came from.
  if (Motion.ok) {
    gsap.from(document.querySelectorAll(".viewer__frame.is-active .evbox"), {
      opacity: 0, scale: 1.1, duration: 0.3, stagger: 0.05, delay: 0.2, ease: Motion.ease, clearProps: "opacity,transform",
    });
  }
})();
