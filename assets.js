/* Harness Engineering — shared client-side interactivity.
 * Quiz engine + localStorage progress. No network, no dependencies.
 * Loaded by every lesson page via <script src="../assets.js"></script>.
 */
(function () {
  "use strict";

  /* ---- Quiz engine ----
   * Markup contract per lesson:
   *   <div class="quiz" data-quiz="m01">
   *     <h3>Check your understanding</h3>
   *     <div class="q" data-answer="1">
   *       <div class="prompt">...</div>
   *       <div class="opts">
   *         <button class="opt">A</button>
   *         <button class="opt">B</button>   <- correct one has data-answer index on .q, not here
   *       </div>
   *       <div class="explain"><b>Why:</b> ...</div>
   *     </div>
   *     ...
   *   </div>
   * The correct option is the one whose index matches data-answer on .q
   * (0-based). Explanations are revealed after a choice is made.
   */
  function initQuiz(q) {
    var key = q.getAttribute("data-quiz");
    var qs = q.querySelectorAll(".q");
    var answered = 0;
    var score = 0;

    qs.forEach(function (qel, qi) {
      var correct = parseInt(qel.getAttribute("data-answer"), 10);
      var opts = qel.querySelectorAll(".opt");
      var explain = qel.querySelector(".explain");
      opts.forEach(function (opt, oi) {
        opt.addEventListener("click", function () {
          if (qel.dataset.done) return;
          qel.dataset.done = "1";
          opts.forEach(function (o, i) {
            o.disabled = true;
            if (i === correct) o.classList.add("correct");
          });
          if (oi === correct) {
            score++;
          } else {
            opt.classList.add("wrong");
          }
          if (explain) explain.classList.add("show");
          answered++;
          if (answered === qs.length) finish();
        });
      });
    });

    function finish() {
      var bar = q.querySelector(".scorebar");
      if (!bar) {
        bar = document.createElement("div");
        bar.className = "scorebar";
        q.appendChild(bar);
      }
      var pct = Math.round((score / qs.length) * 100);
      bar.innerHTML =
        '<span>Score</span><span class="pct">' + score + "/" + qs.length +
        " · " + pct + "%</span>";
      var btn = document.createElement("button");
      btn.textContent = "Retake";
      btn.addEventListener("click", function () {
        location.reload();
      });
      bar.appendChild(btn);
      bar.classList.add("show");
      save(key, score, qs.length);
    }
  }

  /* ---- Progress in localStorage ---- */
  var NS = "he_progress_v1";
  function save(mod, score, total) {
    try {
      var all = JSON.parse(localStorage.getItem(NS) || "{}");
      all[mod] = { score: score, total: total, at: Date.now() };
      localStorage.setItem(NS, JSON.stringify(all));
      updateIndex();
    } catch (e) {}
  }
  function load() {
    try {
      return JSON.parse(localStorage.getItem(NS) || "{}");
    } catch (e) {
      return {};
    }
  }

  /* If an index page element #scoreboard exists, render totals there. */
  function updateIndex() {
    var sb = document.getElementById("scoreboard");
    if (!sb) return;
    var all = load();
    var done = Object.keys(all).length;
    var pcts = Object.keys(all).map(function (k) {
      return all[k].score / all[k].total;
    });
    var avg = pcts.length
      ? Math.round((pcts.reduce(function (a, b) { return a + b; }, 0) / pcts.length) * 100)
      : 0;
    sb.innerHTML =
      "<strong>" + done + "</strong> modules attempted · " +
      "<strong>" + avg + "%</strong> average";
  }

  /* ---- Interactive: H-ladder accordion ---- */
  function initLadder(root) {
    root.querySelectorAll(".lr").forEach(function (el) {
      el.addEventListener("click", function () {
        el.classList.toggle("open");
      });
    });
  }

  /* ---- Interactive: flip cards ---- */
  function initCards(root) {
    root.querySelectorAll(".card").forEach(function (el) {
      el.addEventListener("click", function () {
        el.classList.toggle("flipped");
      });
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".quiz").forEach(initQuiz);
    document.querySelectorAll(".ladder").forEach(initLadder);
    document.querySelectorAll(".cards").forEach(initCards);
    updateIndex();
  });
})();
