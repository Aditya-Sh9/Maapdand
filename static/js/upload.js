/* Upload page: keeps one list of chosen images (from the picker, drag-and-drop and the camera),
   shows a tile per image with a quick size check, and shows progress while the server reads them. */
(function () {
  var MAX_IMAGES = 6;
  var MAX_MB = 10;
  var MIN_SIDE = 800; // same threshold as extraction/preprocess.py

  var form = document.getElementById("upload-form");
  var input = document.getElementById("images");
  var camera = document.getElementById("camera");
  var cameraBtn = document.getElementById("camera-btn");
  var dropzone = document.getElementById("dropzone");
  var tiles = document.getElementById("tiles");
  var files = []; // the single source of truth; copied into `input` before submit

  // A browser replaces a file input's list on every pick, so we keep our own list
  // and write it back with DataTransfer (the only way to set input.files).
  function syncInput() {
    var dt = new DataTransfer();
    files.forEach(function (f) { dt.items.add(f); });
    input.files = dt.files;
  }

  function addFiles(list) {
    Array.from(list).forEach(function (f) {
      if (!f.type.startsWith("image/")) return;
      var dup = files.some(function (g) { return g.name === f.name && g.size === f.size; });
      if (!dup && files.length < MAX_IMAGES) files.push(f);
    });
    syncInput();
    render();
  }

  function statusFor(file, img) {
    if (file.size > MAX_MB * 1024 * 1024) return ["is-warn", "triangle-alert", "Over " + MAX_MB + " MB"];
    if (Math.max(img.naturalWidth, img.naturalHeight) < MIN_SIDE) return ["is-warn", "triangle-alert", "Low resolution, may be rejected"];
    return ["is-ok", "circle-check", "Looks usable"];
  }

  var ICONS = { // tiny inline copies of the Lucide icons used in tiles
    "circle-check": '<circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/>',
    "triangle-alert": '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
    "x": '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
  };
  function svg(name, size) {
    return '<svg class="icon" width="' + size + '" height="' + size + '" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + ICONS[name] + "</svg>";
  }

  function render() {
    tiles.innerHTML = "";
    files.forEach(function (file, i) {
      var li = document.createElement("li");
      li.className = "tile";
      var url = URL.createObjectURL(file);
      li.innerHTML =
        '<img alt="" src="' + url + '">' +
        '<div class="tile__meta"><span class="tile__name"></span><span class="tile__status">Checking…</span></div>' +
        '<button type="button" class="tile__remove">' + svg("x", 18) + '<span class="visually-hidden">Remove image ' + (i + 1) + "</span></button>";
      li.querySelector(".tile__name").textContent = "Image " + (i + 1) + " · " + file.name;
      var img = li.querySelector("img");
      img.onload = function () {
        var s = statusFor(file, img);
        var status = li.querySelector(".tile__status");
        status.className = "tile__status " + s[0];
        status.innerHTML = svg(s[1], 14) + "<span></span>";
        status.lastChild.textContent = s[2];
        URL.revokeObjectURL(url);
      };
      li.querySelector(".tile__remove").addEventListener("click", function () {
        files.splice(i, 1);
        syncInput();
        render();
        input.focus();
      });
      tiles.appendChild(li);
      if (Motion.ok) gsap.from(li, { opacity: 0, y: 6, duration: 0.25, ease: Motion.ease });
    });
    var title = dropzone.querySelector(".dropzone__title");
    title.textContent = files.length ? "Add another side (" + files.length + " of " + MAX_IMAGES + ")" : "Choose photos of the pack";
  }

  input.addEventListener("change", function () {
    // The picker just replaced input.files; merge those into our list.
    var picked = Array.from(input.files);
    addFiles(picked);
  });
  camera.addEventListener("change", function () { addFiles(camera.files); camera.value = ""; });
  cameraBtn.addEventListener("click", function () { camera.click(); });

  ["dragenter", "dragover"].forEach(function (type) {
    dropzone.addEventListener(type, function (e) { e.preventDefault(); dropzone.classList.add("is-over"); });
  });
  ["dragleave", "drop"].forEach(function (type) {
    dropzone.addEventListener(type, function () { dropzone.classList.remove("is-over"); });
  });
  dropzone.addEventListener("drop", function (e) { e.preventDefault(); addFiles(e.dataTransfer.files); });

  // While the server runs OCR the page is idle for a while: show it is working and move the stepper to "Read".
  form.addEventListener("submit", function () {
    var btn = document.getElementById("submit-btn");
    btn.disabled = true;
    btn.querySelector("span").textContent = "Reading…";
    form.classList.add("is-busy");
    if (files.length) {
      document.getElementById("busy-text").textContent =
        "Reading " + files.length + (files.length === 1 ? " image" : " images") + " in English and Hindi. This usually takes 10 to 30 seconds.";
    }
    var stepper = document.querySelector(".stepper");
    if (stepper) {
      var steps = stepper.querySelectorAll(".stepper__step");
      steps[0].classList.replace("is-current", "is-done");
      steps[0].removeAttribute("aria-current");
      steps[0].querySelector(".stepper__dot").innerHTML =
        '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.25" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>';
      steps[1].classList.replace("is-todo", "is-current");
      steps[1].setAttribute("aria-current", "step");
      stepper.dataset.current = "2";
      var fill = stepper.querySelector(".stepper__fill");
      if (Motion.ok) gsap.fromTo(fill, { width: "12.5%" }, { width: "37.5%", duration: 0.4, ease: Motion.ease });
    }
  });

  var problems = document.getElementById("problems");
  if (problems) problems.focus();
})();
