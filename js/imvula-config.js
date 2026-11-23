(function () {
  var PROD_API_BASE_URL = "https://imvula-os-api.example.com";
  var host = window.location.hostname;

  var isLocal =
    host === "localhost" ||
    host === "127.0.0.1" ||
    host === "" ||
    /^\d+\.\d+\.\d+\.\d+$/.test(host);

  var apiHost = (host === "" || host === "localhost" || host === "127.0.0.1")
    ? "localhost"
    : host;

  window.IMVULA = window.IMVULA || {};
  window.IMVULA.API_BASE_URL = isLocal
    ? "http://" + apiHost + ":8000"
    : PROD_API_BASE_URL;
  window.IMVULA.IS_LOCAL = isLocal;

  window.IMVULA.url = function (relPath) {
    var inPages = window.location.pathname.indexOf("/pages/") !== -1;
    return inPages ? "../" + relPath : relPath;
  };
})();
