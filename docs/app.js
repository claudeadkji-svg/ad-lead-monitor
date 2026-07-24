/* AD LEAD MONITOR — 대시보드 로직 */
(function () {
  "use strict";

  var CFG = window.SITE_CONFIG || {};
  var REPO = "claudeadkji-svg/ad-lead-monitor";
  var STATUS_PATH = "docs/data/status.json";
  var state = { dates: [], date: null, snapshot: null, newOnly: false, status: {} };

  var CAT_ORDER = [
    "정부·공공 입찰", "신규 캠페인·브랜드", "채용공고 리드",
    "업계 협회·뉴스", "기타 뉴스 리드", "수동 등록",
  ];
  var STATUS_OPTIONS = ["", "컨택예정", "메일발송", "회신받음", "미팅", "보류"];

  /* ── 비밀번호 게이트 ─────────────────── */
  function sha256(str) {
    return crypto.subtle.digest("SHA-256", new TextEncoder().encode(str)).then(function (buf) {
      return Array.prototype.map.call(new Uint8Array(buf), function (b) {
        return b.toString(16).padStart(2, "0");
      }).join("");
    });
  }

  function tryLogin() {
    sha256(document.getElementById("pw").value).then(function (h) {
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
    return fetch(path + (path.indexOf("?") < 0 ? "?t=" + Date.now() : "")).then(function (r) {
      if (!r.ok) throw new Error(path + " " + r.status);
      return r.json();
    });
  }

  function loadStatus() {
    // raw.githubusercontent = 커밋 즉시 반영 (Pages 배포 지연 회피)
    return fetchJson("https://raw.githubusercontent.com/" + REPO + "/main/" + STATUS_PATH)
      .catch(function () { return fetchJson("data/status.json"); })
      .then(function (st) { state.status = st || {}; })
      .catch(function () { state.status = {}; });
  }

  function init() {
    Promise.all([fetchJson("data/index.json"), loadStatus()]).then(function (res) {
      state.dates = res[0].dates || [];
      var sel = document.getElementById("date-sel");
      sel.innerHTML = state.dates.map(function (d, i) {
        return '<option value="' + d + '">' + d + (i === 0 ? " (최신)" : "") + "</option>";
      }).join("");
      if (state.dates.length) loadDate(state.dates[0]);
      else document.getElementById("sections").innerHTML = '<div class="empty">아직 수집된 데이터가 없습니다.</div>';
    }).catch(function () {
      document.getElementById("sections").innerHTML = '<div class="empty">데이터 로드 실패 — data/index.json 확인 필요</div>';
    });
    loadReports();
  }

  function loadDate(d) {
    state.date = d;
    fetchJson("data/" + d + ".json").then(function (snap) {
      state.snapshot = snap;
      buildFilters(snap);
      render();
    });
  }

  function loadReports() {
    fetchJson("reports/index.json").then(function (idx) {
      var el = document.getElementById("reports");
      if (!idx.reports || !idx.reports.length) return;
      el.innerHTML = "<h3>📁 주간 엑셀 리포트</h3><ul>" +
        idx.reports.map(function (r) {
          return '<li><a href="reports/' + esc(r.file) + '">' + esc(r.label) + "</a></li>";
        }).join("") + "</ul>";
    }).catch(function () { /* 리포트 없으면 무시 */ });
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

  function statusCell(it) {
    var st = state.status[it.id] || {};
    var opts = STATUS_OPTIONS.map(function (o) {
      return '<option value="' + o + '"' + (o === (st.s || "") ? " selected" : "") + ">" +
        (o || "—") + "</option>";
    }).join("");
    var who = st.by ? '<div class="st-by">' + esc(st.by) + " · " + esc(st.at || "") + "</div>" : "";
    return '<select class="st-sel st-' + (st.s || "none") + '" data-id="' + esc(it.id) + '">' +
      opts + "</select>" + who;
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
        '<th class="chk"><input type="checkbox" class="cat-all"></th>' +
        "<th>제목</th><th>거래처</th><th>소스</th><th>연락처</th><th>상태</th><th>최초 등록</th>" +
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
            '<td class="status">' + statusCell(it) + "</td>" +
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

    Array.prototype.forEach.call(document.querySelectorAll(".cat-all"), function (cb) {
      cb.addEventListener("change", function () {
        Array.prototype.forEach.call(cb.closest("table").querySelectorAll(".row-chk"), function (c) {
          c.checked = cb.checked;
        });
      });
    });
    Array.prototype.forEach.call(document.querySelectorAll(".st-sel"), function (sel) {
      sel.addEventListener("change", function () {
        saveStatus(sel.getAttribute("data-id"), sel.value, sel);
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

  /* ── 상태 저장 (GitHub API) ─────────────────── */
  function ghToken() { return localStorage.getItem("alm_gh_token") || ""; }
  function ghName() { return localStorage.getItem("alm_gh_name") || "팀원"; }

  function saveStatus(id, value, sel) {
    if (!ghToken()) {
      alert("상태를 저장하려면 우측 상단 ⚙ 설정에서 GitHub 토큰을 등록해야 합니다.\n(등록 방법은 설정 창 안내 참고)");
      openSettings();
      render();
      return;
    }
    sel.disabled = true;
    var api = "https://api.github.com/repos/" + REPO + "/contents/" + STATUS_PATH;
    var headers = {
      "Authorization": "Bearer " + ghToken(),
      "Accept": "application/vnd.github+json",
    };
    fetch(api + "?ref=main&t=" + Date.now(), { headers: headers })
      .then(function (r) { if (!r.ok) throw new Error("read " + r.status); return r.json(); })
      .then(function (file) {
        var cur = {};
        try {
          cur = JSON.parse(decodeURIComponent(escape(atob(file.content.replace(/\n/g, "")))));
        } catch (e) { cur = {}; }
        var today = new Date().toISOString().slice(0, 10);
        if (value) cur[id] = { s: value, by: ghName(), at: today };
        else delete cur[id];
        var body = {
          message: "status: " + (value || "해제") + " by " + ghName(),
          content: btoa(unescape(encodeURIComponent(JSON.stringify(cur, null, 1)))),
          sha: file.sha,
          branch: "main",
        };
        return fetch(api, { method: "PUT", headers: headers, body: JSON.stringify(body) });
      })
      .then(function (r) {
        if (!r.ok) throw new Error("write " + r.status);
        state.status[id] = value ? { s: value, by: ghName(), at: new Date().toISOString().slice(0, 10) } : undefined;
        if (!value) delete state.status[id];
        sel.disabled = false;
        sel.className = "st-sel st-" + (value || "none");
      })
      .catch(function (e) {
        sel.disabled = false;
        alert("상태 저장 실패: " + e.message + "\n토큰 권한(Contents: Read and write)을 확인하세요.");
        render();
      });
  }

  /* ── 설정 모달 ─────────────────── */
  function openSettings() {
    document.getElementById("settings").style.display = "flex";
    document.getElementById("set-name").value = localStorage.getItem("alm_gh_name") || "";
    document.getElementById("set-token").value = localStorage.getItem("alm_gh_token") || "";
  }
  document.getElementById("settings-btn").addEventListener("click", openSettings);
  document.getElementById("set-save").addEventListener("click", function () {
    localStorage.setItem("alm_gh_name", document.getElementById("set-name").value.trim());
    localStorage.setItem("alm_gh_token", document.getElementById("set-token").value.trim());
    document.getElementById("settings").style.display = "none";
  });
  document.getElementById("set-close").addEventListener("click", function () {
    document.getElementById("settings").style.display = "none";
  });

  /* ── 엑셀 다운로드 ─────────────────── */
  function exportItems(items) {
    if (!items.length) { alert("다운로드할 항목이 없습니다. 체크박스로 선택해 주세요."); return; }
    var rows = items.map(function (it) {
      var st = state.status[it.id] || {};
      return {
        "날짜": state.date, "카테고리": it.category, "소스": it.source,
        "제목": it.title, "거래처": it.company, "링크": it.url,
        "이메일": it.email, "전화번호": it.phone,
        "설명": it.description, "최초등록일": it.first_seen,
        "신규": it.is_new ? "NEW" : "", "상태": st.s || "", "담당": st.by || "",
      };
    });
    var name = "ad_leads_" + state.date;
    if (window.XLSX) {
      var ws = XLSX.utils.json_to_sheet(rows);
      ws["!cols"] = [{wch:11},{wch:14},{wch:12},{wch:50},{wch:18},{wch:40},{wch:24},{wch:14},{wch:40},{wch:11},{wch:6},{wch:9},{wch:9}];
      var wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb, ws, "leads");
      XLSX.writeFile(wb, name + ".xlsx");
    } else {
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
