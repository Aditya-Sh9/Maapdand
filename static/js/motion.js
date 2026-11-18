/* Shared motion. DESIGN.md: motion explains progress or a verdict, ease-out only,
   and nothing moves when the person has asked for reduced motion. */
window.Motion = (function () {
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var ok = !reduce && typeof window.gsap !== "undefined";
  return { ok: ok, ease: "power3.out" };
})();

/* Stepper: the progress line grows from the previous step to this one. */
(function () {
  var stepper = document.querySelector(".stepper");
  if (!stepper || !Motion.ok) return;
  var current = Number(stepper.dataset.current || 1);
  var widths = { 1: 0, 2: 12.5, 3: 37.5, 4: 62.5 };
  gsap.from(stepper.querySelector(".stepper__fill"), {
    width: widths[current] + "%", duration: 0.4, delay: 0.1, ease: Motion.ease,
  });
})();
