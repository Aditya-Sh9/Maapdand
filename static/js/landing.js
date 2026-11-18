/* Landing page only: Lenis smooth scroll, the sample-label sequence, and gentle section entrances. */
(function () {
  if (!Motion.ok) return; // reduced motion: everything is already visible, nothing to do

  // Lenis smooths wheel scrolling on this long page; app pages keep native scroll.
  if (window.Lenis) {
    var lenis = new Lenis({ duration: 1.0, easing: function (t) { return 1 - Math.pow(1 - t, 3); } });
    (function raf(time) { lenis.raf(time); requestAnimationFrame(raf); })(performance.now());
  }

  // Sample label: each evidence box draws in, then its check resolves to a verdict.
  var specimen = document.querySelector("[data-specimen]");
  if (specimen) {
    var rows = specimen.querySelectorAll(".specimen__checks li");
    var boxes = {};
    specimen.querySelectorAll(".ev").forEach(function (ev) {
      var tag = ev.querySelector(".ev__tag");
      if (tag) boxes[tag.textContent.trim()] = ev.querySelector(".ev__box") || ev;
    });
    var tl = gsap.timeline({ delay: 0.35, defaults: { ease: Motion.ease } });
    rows.forEach(function (row, i) {
      var at = i * 0.11;
      var box = boxes[row.querySelector(".code").textContent.trim()];
      if (box) tl.from(box, { opacity: 0, scale: 1.06, duration: 0.3 }, at);
      tl.from(row.querySelector(".chip"), { opacity: 0, x: -6, duration: 0.25 }, at + 0.12);
    });
  }

  // Sections below the fold rise in once as they enter the viewport.
  var targets = [];
  document.querySelectorAll("[data-reveal]").forEach(function (el) { targets.push([el]); });
  document.querySelectorAll("[data-reveal-group]").forEach(function (el) { targets.push(Array.from(el.children)); });
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (!entry.isIntersecting) return;
      io.unobserve(entry.target);
      gsap.to(entry.target._group, { opacity: 1, y: 0, duration: 0.4, stagger: 0.06, ease: Motion.ease });
    });
  }, { rootMargin: "0px 0px -10% 0px" });
  targets.forEach(function (group) {
    var first = group[0];
    if (!first || first.getBoundingClientRect().top < window.innerHeight) return; // already on screen
    gsap.set(group, { opacity: 0, y: 12 });
    first._group = group;
    io.observe(first);
  });
})();
