/* Report page: the button opens the browser's print window, where "Save as PDF" makes the file. */
(function () {
  var btn = document.getElementById("print-btn");
  if (btn) btn.addEventListener("click", function () { window.print(); });
})();
