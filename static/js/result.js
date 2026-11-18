/* Result page: the verdict sequence. The donut fills, the passed count runs up,
   and the rule rows resolve one after another (under 900 ms in total). */
(function () {
  if (!Motion.ok) return;
  var tl = gsap.timeline({ defaults: { ease: Motion.ease } });

  // Donut: each segment draws along the ring from where the previous one ended.
  document.querySelectorAll(".donut circle:not(.track)").forEach(function (seg, i) {
    var length = parseFloat(seg.getAttribute("stroke-dasharray"));
    var offset = parseFloat(seg.getAttribute("stroke-dashoffset"));
    tl.fromTo(seg, { attr: { "stroke-dasharray": "0 999" } },
      { attr: { "stroke-dasharray": length + " 999", "stroke-dashoffset": offset }, duration: 0.35 }, i * 0.12);
  });

  // Count up the passed number in the centre.
  var num = document.querySelector("[data-count]");
  if (num) {
    var target = Number(num.dataset.count);
    var rest = num.innerHTML.replace(/^\d+/, "");
    var counter = { v: 0 };
    tl.to(counter, {
      v: target, duration: 0.6, ease: "power2.out",
      onUpdate: function () { num.innerHTML = Math.round(counter.v) + rest; },
    }, 0);
  }

  // Rule rows resolve one by one: row first, then its verdict chip.
  var rows = document.querySelectorAll(".rules > li");
  var step = Math.min(0.06, 0.6 / Math.max(rows.length, 1));
  rows.forEach(function (li, i) {
    tl.from(li, { opacity: 0, y: 6, duration: 0.25, clearProps: "opacity,transform" }, 0.1 + i * step);
    tl.from(li.querySelector(".chip"), { opacity: 0, scale: 0.9, duration: 0.2, clearProps: "opacity,transform" }, 0.2 + i * step);
  });
})();
