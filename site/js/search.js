// Client-side search over /index.json (built by site/build.py). Every word must match;
// title hits rank above tag hits, which rank above body hits.
(function () {
  var input = document.getElementById("searchInput");
  var status = document.getElementById("searchStatus");
  var list = document.getElementById("searchResults");
  var index = null;

  function esc(s) {
    return s.replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function count(hay, word) {
    var n = 0, i = hay.indexOf(word);
    while (i !== -1) { n++; i = hay.indexOf(word, i + word.length); }
    return n;
  }

  function snippet(text, words) {
    var lower = text.toLowerCase(), at = -1;
    words.forEach(function (w) { var i = lower.indexOf(w); if (i !== -1 && (at === -1 || i < at)) at = i; });
    if (at === -1) return esc(text.slice(0, 160)) + (text.length > 160 ? "…" : "");
    var start = Math.max(0, at - 60), end = Math.min(text.length, at + 120);
    var out = esc(text.slice(start, end));
    words.forEach(function (w) {
      out = out.replace(new RegExp("(" + esc(w).replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + ")", "gi"), "<mark>$1</mark>");
    });
    return (start > 0 ? "…" : "") + out + (end < text.length ? "…" : "");
  }

  function run() {
    var q = input.value.trim();
    var url = new URL(location.href);
    if (q) url.searchParams.set("q", q); else url.searchParams.delete("q");
    history.replaceState(null, "", url);
    list.innerHTML = "";
    if (!q) { status.textContent = ""; return; }
    if (!index) { status.textContent = "Loading…"; return; }
    var words = q.toLowerCase().split(/\s+/);
    var hits = [];
    index.forEach(function (e) {
      var title = e.title.toLowerCase(), tags = e.tags.join(" ").toLowerCase(), text = e.text.toLowerCase();
      var score = 0;
      for (var i = 0; i < words.length; i++) {
        var w = words[i], s = count(title, w) * 20 + count(tags, w) * 8 + Math.min(count(text, w), 10);
        if (!s) return;
        score += s;
      }
      hits.push({ e: e, score: score });
    });
    hits.sort(function (a, b) { return b.score - a.score || (b.e.date > a.e.date ? 1 : -1); });
    status.textContent = hits.length ? hits.length + " result" + (hits.length === 1 ? "" : "s") : "No results.";
    list.innerHTML = hits.slice(0, 30).map(function (h) {
      var e = h.e;
      return '<li class="search-hit"><a href="' + esc(e.url) + '">' + esc(e.title) + "</a>" +
        '<div class="search-meta">' + esc([e.section, e.date].filter(Boolean).join(" · ")) + "</div>" +
        '<p class="search-snippet">' + snippet(e.text, words) + "</p></li>";
    }).join("");
  }

  input.value = new URLSearchParams(location.search).get("q") || "";
  input.addEventListener("input", run);
  input.addEventListener("keydown", function (ev) {
    if (ev.key === "Escape") { input.value = ""; run(); }
    if (ev.key === "Enter") { var a = list.querySelector("a"); if (a) location.href = a.href; }
  });
  fetch("/index.json").then(function (r) { return r.json(); }).then(function (data) {
    index = data;
    run();
  }).catch(function () { status.textContent = "Couldn't load the search index."; });
})();
