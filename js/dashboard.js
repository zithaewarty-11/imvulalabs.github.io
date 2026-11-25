/*
 * Imvula OS — Live Dashboard
 * Requires imvula-config.js and imvula-auth.js first.
 */
(function () {
  "use strict";

  var auth = window.ImvulaAuth;

  if (!auth) {
    console.error("Imvula OS authentication client is unavailable.");
    return;
  }

  var banner = document.getElementById("statusBanner");
  var logoutLink = document.getElementById("logoutLink");
  var riskBody = document.getElementById("riskTableBody");

  function setBanner(message, type) {
    banner.textContent = message;

    if (type === "error") {
      banner.style.background = "#fef2f2";
      banner.style.color = "#991b1b";
    } else if (type === "success") {
      banner.style.background = "#ecfdf5";
      banner.style.color = "#065f46";
    } else {
      banner.style.background = "#eef2ff";
      banner.style.color = "#3730a3";
    }
  }

  function showCellMessage(message) {
    riskBody.replaceChildren();

    var row = document.createElement("tr");
    var cell = document.createElement("td");

    cell.colSpan = 4;
    cell.textContent = message;
    cell.style.textAlign = "center";
    cell.style.color = "var(--muted)";

    row.appendChild(cell);
    riskBody.appendChild(row);
  }

  function normalizeList(response, possibleKeys) {
    if (Array.isArray(response)) {
      return response;
    }

    if (response && typeof response === "object") {
      for (var i = 0; i < possibleKeys.length; i++) {
        var value = response[possibleKeys[i]];

        if (Array.isArray(value)) {
          return value;
        }
      }
    }

    return [];
  }

  function safeClass(value) {
    return String(value || "unknown")
      .toLowerCase()
      .replace(/[^a-z0-9_-]/g, "");
  }

  function addCell(row, value) {
    var cell = document.createElement("td");
    cell.textContent = value == null ? "—" : String(value);
    row.appendChild(cell);
  }

  function addBadgeCell(row, value) {
    var cell = document.createElement("td");
    var badge = document.createElement("span");

    badge.className = "badge " + safeClass(value);
    badge.textContent = value == null ? "Unknown" : String(value);

    cell.appendChild(badge);
    row.appendChild(cell);
  }

  function renderRisks(risks) {
    riskBody.replaceChildren();

    if (!risks.length) {
      showCellMessage("No risks have been recorded yet.");
      return;
    }

    risks.slice(0, 10).forEach(function (risk) {
      var row = document.createElement("tr");

      addCell(row, "#" + risk.id);
      addCell(row, risk.title);
      addBadgeCell(row, risk.severity);
      addBadgeCell(row, risk.status);

      riskBody.appendChild(row);
    });
  }

  function renderRiskCounts(risks) {
    var counts = {
      critical: 0,
      high: 0,
      medium: 0,
      low: 0
    };

    risks.forEach(function (risk) {
      var severity = String(risk.severity || "").toLowerCase();

      if (Object.prototype.hasOwnProperty.call(counts, severity)) {
        counts[severity]++;
      }
    });

    document.getElementById("countCritical").textContent = counts.critical;
    document.getElementById("countHigh").textContent = counts.high;
    document.getElementById("countMedium").textContent = counts.medium;
    document.getElementById("countLow").textContent = counts.low;
  }

  function renderAssets(assets) {
    document.getElementById("assetCount").textContent = assets.length;

    document.getElementById("assetSummary").textContent =
      assets.length === 0
        ? "No assets yet. Add one on the Assets page."
        : assets.length + " asset" +
          (assets.length === 1 ? "" : "s") + " tracked.";
  }

  function loadDashboard() {
    if (!auth.isLoggedIn()) {
      window.location.href = window.IMVULA.url("pages/login.html");
      return;
    }

    setBanner("Loading your Imvula OS workspace...");

    auth.me()
      .then(function (user) {
        if (!user) {
          throw new Error("Your user profile could not be loaded.");
        }

        var email = user.email || "User";
        var role = user.role || "Member";
        var organisation = user.org_id != null
          ? "Organisation #" + user.org_id
          : "Organisation";

        setBanner(
          "Signed in as " + email + " · " +
          organisation + " · Role: " + role,
          "success"
        );

        document.getElementById("orgBadge").textContent = role;
        document.getElementById("userFooter").textContent =
          email + " · " + role;

        return Promise.all([
          auth.api("/quantum/assets"),
          auth.api("/quantum/risks")
        ]);
      })
      .then(function (results) {
        var assets = normalizeList(results[0], ["assets", "items", "data"]);
        var risks = normalizeList(results[1], ["risks", "items", "data"]);

        renderAssets(assets);
        renderRiskCounts(risks);
        renderRisks(risks);
      })
      .catch(function (error) {
        console.error("Imvula OS dashboard error:", error);

        setBanner(
          error.message || "Unable to load your dashboard.",
          "error"
        );

        showCellMessage(
          "Dashboard data could not be loaded. Please refresh and try again."
        );
      });
  }

  if (logoutLink) {
    logoutLink.addEventListener("click", function (event) {
      event.preventDefault();
      auth.logout();
    });
  }

  loadDashboard();
})();
