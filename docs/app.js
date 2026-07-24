/* AD LEAD MONITOR — 대시보드 로직 */
(function () {
  "use strict";

  var CFG = window.SITE_CONFIG || {};
  var state = { dates: [], date: null, snapshot: null, newOnly: false };

  var CAT_ORDER = [
    "정부·공공 입찰", "신규 캠페인·브랜드", "채용공고 리드",
    "업계 협회·뉴스", "기타 뉴스 리드", "수동 등록",
  ];

  /* ── 비밀번호 게이트 ─────────────────── */
  function sha256(str) {
    return crypto.subtle.digest("SHA-256", new TextEncoder().encode(str)).then(function (buf) {
      return Array.prototype.map.call(new Uint8Array(buf), function (b) {
        return b.toString(16).padStart(2, "0");
      }).join("");
    });
  }

  function tryLogin() {
    var pw = document.getElementById("pw").value;
    sha256(pw).then(function (h) {
      if (h === CFG.PASSWORD_HASH) {
        sessionStorage.setItem("alm_auth", h);
        unlock();
      } else {
        document.getElementById("pw-err").textContent = "비밀번호가 올바르지 않습니다.";
      }
    });
  }

  function unlock() {
    document.getElementById("gate").style.display = "none";
    document.getElementById("app").style.display = "";
    init();
  }

  document.getElementById("pw-btn").addEventListener("click", tryLogin);
  document.getElementById("pw").addEventListener("keydown", function (e) {
    if (e.key === "Enter") tryLogin();
  });
  if (sessionStorage.getItem("alm_auth") === CFG.PASSWORD_HASH) unlock();

  /* ── 데이터 로드 ─────────────────── */
  function fetchJson(path) {
    return fetch(path + "?t=" + Date.now()).then(function (r) {
      if (!r.ok) throw new Error(path + " " + r.status);
      return r.json();
    });
  }

  function init() {
    fetchJson("data/index.json").then(function (idx) {
      state.dates = idx.dates || [];
      var sel = document.getElementById("date-sel");
      sel.innerHTML = state.dates.map(function (d, i) {
        return '<option value="' + d + '">' + d + (i === 0 ? " (최신)" : "") + "</option>";
      }).join("");
      if (state.dates.length) loadDate(state.dates[0]);
      else document.getElementById("sections").innerHTML = '<div class="empty">아직 수집된 데이터가 없습니다.</div>';
    }).catch(function () {
      document.getElementById("sections").innerHTML = '<div class="empty">데이터 로드 실패 — data/index.json 확인 필요</div>';
    });
  }

  function loadDate(d) {
    state.date = d;
    fetchJson("data/" + d + ".json").then(function (snap) {
      state.snapshot = snap;
      buildFilters(snap);
      render();
    });
  }

  function buildFilters(snap) {
    var cats = {}, srcs = {};
    snap.items.forEach(function (it) { cats[it.category] = 1; srcs[it.source] = 1; });
    var catSel = document.getElementById("cat-sel");
    var cur = catSel.value;
    catSel.innerHTML = '<option value="">전체 카테고리</option>' +
      Object.keys(cats).sort(catCmp).map(function (c) {
        return '<option' + (c === cur ? " selected" : "") + ">" + c + "</option>";
      }).join("");
    var srcSel = document.getElementById("src-sel");
    var cur2 = srcSel.value;
    srcSel.innerHTML = '<option value="">전체 소스</option>' +
      Object.keys(srcs).sort().map(function (s) {
        return '<option' + (s === cur2 ? " selected" : "") + ">" + s + "</option>";
      }).join("");
  }

  function catCmp(a, b) {
    var ia = CAT_ORDER.indexOf(a), ib = CAT_ORDER.indexOf(b);
    if (ia < 0) ia = 99; if (ib < 0) ib = 99;
    return ia - ib || a.localeCompare(b);
  }

  /* ── 렌더링 ─────────────────── */
  function esc(s) {
    return String(s || "").replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function filtered() {
    var q = document.getElementById("search").value.trim().toLowerCase();
    var cat = document.getElementById("cat-sel").value;
    var src = document.getElementById("src-sel").value;
    return state.snapshot.items.filter(function (it) {
      if (state.newOnly && !it.is_new) return false;
      if (cat && it.category !== cat) return false;
      if (src && it.source !== src) return false;
      if (q) {
        var hay = (it.title + " " + it.company + " " + it.description + " " + it.source).toLowerCase();
        if (hay.indexOf(q) < 0) return false;
      }
      return true;
    });
  }

  function contactCell(it) {
    var parts = [];
    if (it.email) parts.push('<a href="mailto:' + esc(it.email) + '">' + esc(it.email) + "</a>");
    if (it.phone) parts.push('<a href="tel:' + esc(it.phone) + '">' + esc(it.phone) + "</a>");
    if (!it.email && !it.phone && it.company) {
      parts.push('<a class="find" target="_blank" rel="noopener" href="https://search.naver.com/search.naver?query=' +
        encodeURIComponent(it.company + " 대표번호") + '">🔍 연락처 찾기</a>');
    }
    return parts.join("<br>") || '<span class="find">—</span>';
  }

  function render() {
    var items = filtered();
    var byCat = {};
    items.forEach(function (it) { (byCat[it.category] = byCat[it.category] || []).push(it); });

    var html = Object.keys(byCat).sort(catCmp).map(function (cat) {
      var rows = byCat[cat];
      var newCnt = rows.filter(function (r) { return r.is_new; }).length;
      return (
        '<section class="cat-section">' +
        '<div class="cat-head"><h2>' + esc(cat) + '</h2>' +
        '<span class="cnt">' + rows.length + "건</span>" +
        (newCnt ? '<span class="newcnt">신규 ' + newCnt + "건</span>" : "") +
        "</div><table><thead><tr>" +
        '<th class="chk"><input type="checkbox" class="cat-all" data-cat="' + esc(cat) + '"></th>' +
        "<th>제목</th><th>거래처</th><th>소스</th><th>연락처</th><th>최초 등록</th>" +
        "</tr></thead><tbody>" +
        rows.map(function (it) {
          return (
            '<tr class="' + (it.is_new ? "new-item" : "") + '">' +
            '<td class="chk"><input type="checkbox" class="row-chk" data-id="' + esc(it.id) + '"></td>' +
            '<td class="title">' + (it.is_new ? '<span class="badge-new">NEW</span>' : "") +
            '<a href="' + esc(it.url) + '" target="_blank" rel="noopener">' + esc(it.title) + "</a>" +
            (it.description ? '<div class="desc">' + esc(it.description) + "</div>" : "") + "</td>" +
            '<td class="company" title="' + esc(it.company) + '">' + esc(it.company || "—") + "</td>" +
            '<td class="src">' + esc(it.source) + "</td>" +
            '<td class="contact">' + contactCell(it) + "</td>" +
            '<td class="date">' + esc(it.first_seen || "") + "</td></tr>"
          );
        }).join("") +
        "</tbody></table></section>"
      );
    }).join("");

    document.getElementById("sections").innerHTML =
      html || '<div class="empty">조건에 맞는 항목이 없습니다.</div>';

    var snap = state.snapshot;
    document.getElementById("gen-info").textContent = "업데이트: " + (snap.generated_at || snap.date);
    document.getElementById("stat").innerHTML =
      "표시 " + items.length + "건 / 전체 " + snap.total + "건 · 오늘 신규 <b>" + snap.new_count + "건</b>";

    renderStatus(snap);

    // 카테고리 전체선택
    Array.prototype.forEach.call(document.querySelectorAll(".cat-all"), function (cb) {
      cb.addEventListener("change", function () {
        var table = cb.closest("table");
        Array.prototype.forEach.call(table.querySelectorAll(".row-chk"), function (c) {
          c.checked = cb.checked;
        });
      });
    });
  }

  function renderStatus(snap) {
    var el = document.getElementById("source-status");
    el.innerHTML = "<h3>소스별 수집 상태 (" + esc(snap.date) + ")</h3><ul>" +
      (snap.sources || []).map(function (s) {
        var wait = s.status.indexOf("대기") === 0;
        return '<li class="' + (wait ? "wait" : "") + '"><b>' + esc(s.name) + "</b> — " + esc(s.status) + "</li>";
      }).join("") + "</ul>";
  }

  /* ── 엑셀 다운로드 ─────────────────── */
  function exportItems(items) {
    if (!items.length) { alert("다운로드할 항목이 없습니다. 체크박스로 선택해 주세요."); return; }
    var rows = items.map(function (it) {
      return {
        "날짜": state.date, "카테고리": it.category, "소스": it.source,
        "제목": it.title, "거래처": it.company, "링크": it.url,
        "이메일": it.email, "전화번호": it.phone,
        "설명": it.description, "최초등록일": it.first_seen, "신규": it.is_new ? "NEW" : "",
      };
    });
    var name = "ad_leads_" + state.date;
    if (window.XLSX) {
      var ws = XLSX.utils.json_to_sheet(rows);
      ws["!cols"] = [{wch:11},{wch:14},{wch:12},{wch:50},{wch:18},{wch:40},{wch:24},{wch:14},{wch:40},{wch:11},{wch:6}];
      var wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb, ws, "leads");
      XLSX.writeFile(wb, name + ".xlsx");
    } else {
      // CDN 차단 시 CSV(BOM) 폴백 — 엑셀에서 한글 정상 표시
      var keys = Object.keys(rows[0]);
      var csv = "﻿" + keys.join(",") + "\n" + rows.map(function (r) {
        return keys.map(function (k) {
          return '"' + String(r[k] || "").replace(/"/g, '""') + '"';
        }).join(",");
      }).join("\n");
      var a = document.createElement("a");
      a.href = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
      a.download = name + ".csv";
      a.click();
    }
  }

  document.getElementById("dl-sel").addEventListener("click", function () {
    var ids = {};
    Array.prototype.forEach.call(document.querySelectorAll(".row-chk:checked"), function (c) {
      ids[c.getAttribute("data-id")] = 1;
    });
    exportItems(state.snapshot.items.filter(function (it) { return ids[it.id]; }));
  });
  document.getElementById("dl-all").addEventListener("click", function () {
    exportItems(filtered());
  });

  /* ── 필터 이벤트 ─────────────────── */
  document.getElementById("date-sel").addEventListener("change", function (e) { loadDate(e.target.value); });
  document.getElementById("cat-sel").addEventListener("change", render);
  document.getElementById("src-sel").addEventListener("change", render);
  document.getElementById("search").addEventListener("input", render);
  document.getElementById("new-only").addEventListener("click", function () {
    state.newOnly = !state.newOnly;
    this.classList.toggle("active", state.newOnly);
    render();
  });
})();
