// Imvula OS — Frontend auth + API helper.
// Depends on js/imvula-config.js being loaded first.

(function () {
  var TOKEN_KEY = "imvula_token";
  var USER_KEY = "imvula_user";

  function getToken() {
    try { return localStorage.getItem(TOKEN_KEY); }
    catch (e) { return null; }
  }

  function setToken(t) {
    try { localStorage.setItem(TOKEN_KEY, t); } catch (e) {}
  }

  function clearAuth() {
    try {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(USER_KEY);
    } catch (e) {}
  }

  function getUser() {
    try {
      var raw = localStorage.getItem(USER_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch (e) { return null; }
  }

  function setUser(u) {
    try { localStorage.setItem(USER_KEY, JSON.stringify(u)); } catch (e) {}
  }

  function isLoggedIn() {
    return !!getToken();
  }

  // ─── Core fetch wrapper ───
  // Adds Authorization header if we have a token.
  // Throws Error with .status on non-2xx.
  function api(path, opts) {
    opts = opts || {};
    var url = window.IMVULA.API_BASE_URL + path;
    var headers = opts.headers || {};
    headers["Content-Type"] = "application/json";
    var token = getToken();
    if (token) headers["Authorization"] = "Bearer " + token;

    return fetch(url, {
      method: opts.method || "GET",
      headers: headers,
      body: opts.body ? JSON.stringify(opts.body) : undefined,
    }).then(function (res) {
      if (res.status === 401) {
        clearAuth();
        // Redirect to login only if not already there
        if (window.location.pathname.indexOf("login.html") === -1) {
          window.location.href = window.IMVULA.url("pages/login.html");
        }
        throw Object.assign(new Error("Unauthorized"), { status: 401 });
      }
      return res.text().then(function (text) {
        var data = text ? JSON.parse(text) : null;
        if (!res.ok) {
          var msg = (data && data.detail) ? data.detail : ("HTTP " + res.status);
          throw Object.assign(new Error(msg), { status: res.status, data: data });
        }
        return data;
      });
    });
  }

  // ─── High-level auth ───
  function login(email, password) {
    return api("/auth/login", {
      method: "POST",
      body: { email: email, password: password },
    }).then(function (res) {
      setToken(res.access_token);
      return me();
    });
  }

  function register(email, password, organisation_name) {
    return api("/auth/register", {
      method: "POST",
      body: {
        email: email,
        password: password,
        organisation_name: organisation_name,
      },
    }).then(function (res) {
      setToken(res.access_token);
      return me();
    });
  }

  function me() {
    return api("/auth/me").then(function (u) {
      setUser(u);
      return u;
    });
  }

  function logout() {
    clearAuth();
    window.location.href = window.IMVULA.url("index.html");
  }

  // ─── Export ───
  window.ImvulaAuth = {
    getToken: getToken,
    getUser: getUser,
    isLoggedIn: isLoggedIn,
    login: login,
    register: register,
    me: me,
    logout: logout,
    api: api,
  };
})();
