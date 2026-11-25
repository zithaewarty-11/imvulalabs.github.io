/*
 * Imvula OS — Shared API and authentication client
 * Requires js/imvula-config.js to load first.
 */
(function () {
  "use strict";

  var TOKEN_KEY = "imvula_token";
  var USER_KEY = "imvula_user";

  function getToken() {
    try {
      return localStorage.getItem(TOKEN_KEY);
    } catch (error) {
      return null;
    }
  }

  function setToken(token) {
    if (!token || typeof token !== "string") {
      throw new Error("The API did not return a valid access token.");
    }

    try {
      localStorage.setItem(TOKEN_KEY, token);
    } catch (error) {
      throw new Error("Your browser could not save the login session.");
    }
  }

  function getUser() {
    try {
      var saved = localStorage.getItem(USER_KEY);
      return saved ? JSON.parse(saved) : null;
    } catch (error) {
      return null;
    }
  }

  function setUser(user) {
    try {
      localStorage.setItem(USER_KEY, JSON.stringify(user));
    } catch (error) {
      console.warn("Imvula OS could not save the user profile.");
    }
  }

  function clearAuth() {
    try {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(USER_KEY);
    } catch (error) {
      console.warn("Could not clear the saved session.");
    }
  }

  function isLoggedIn() {
    return Boolean(getToken());
  }

  function getApiUrl(path) {
    var base = window.IMVULA && window.IMVULA.API_BASE_URL;

    if (!base) {
      throw new Error("Imvula API URL is not configured.");
    }

    return base.replace(/\/+$/, "") + "/" +
      String(path || "").replace(/^\/+/, "");
  }

  function api(path, options) {
    options = options || {};

    var headers = new Headers(options.headers || {});
    var token = getToken();
    var body = options.body;
    var requestBody;

    if (token && !headers.has("Authorization")) {
      headers.set("Authorization", "Bearer " + token);
    }

    if (body !== undefined && body !== null) {
      if (body instanceof FormData) {
        requestBody = body;
      } else if (typeof body === "string") {
        requestBody = body;
      } else {
        headers.set("Content-Type", "application/json");
        requestBody = JSON.stringify(body);
      }
    }

    return fetch(getApiUrl(path), {
      method: options.method || "GET",
      headers: headers,
      body: requestBody
    }).then(function (response) {
      return response.text().then(function (raw) {
        var data = null;

        if (raw) {
          try {
            data = JSON.parse(raw);
          } catch (error) {
            data = { detail: raw };
          }
        }

        if (response.status === 401) {
          clearAuth();

          if (
            window.location.pathname.indexOf("login.html") === -1 &&
            window.location.pathname.indexOf("register.html") === -1
          ) {
            window.location.href = window.IMVULA.url("pages/login.html");
          }

          throw Object.assign(
            new Error("Your session has expired. Please sign in again."),
            { status: 401, data: data }
          );
        }

        if (!response.ok) {
          var message = data && data.detail
            ? data.detail
            : "Request failed with HTTP " + response.status;

          if (Array.isArray(message)) {
            message = message.map(function (item) {
              return item.msg || String(item);
            }).join(", ");
          }

          throw Object.assign(new Error(String(message)), {
            status: response.status,
            data: data
          });
        }

        return data;
      });
    }).catch(function (error) {
      if (error.status) {
        throw error;
      }

      throw new Error(
        "Unable to connect to Imvula OS. Check your internet connection or API server."
      );
    });
  }

  function me() {
    return api("/auth/me").then(function (user) {
      setUser(user);
      return user;
    });
  }

  function login(email, password) {
    return api("/auth/login", {
      method: "POST",
      body: {
        email: email.trim().toLowerCase(),
        password: password
      }
    }).then(function (response) {
      setToken(response.access_token);

      return me().catch(function (error) {
        clearAuth();
        throw error;
      });
    });
  }

  function register(email, password, organisationName) {
    return api("/auth/register", {
      method: "POST",
      body: {
        email: email.trim().toLowerCase(),
        password: password,
        organisation_name: organisationName
      }
    }).then(function (response) {
      setToken(response.access_token);

      return me().catch(function (error) {
        clearAuth();
        throw error;
      });
    });
  }

  function logout() {
    clearAuth();
    window.location.href = window.IMVULA.url("index.html");
  }

  function requireAuth() {
    if (!isLoggedIn()) {
      window.location.href = window.IMVULA.url("pages/login.html");
      return false;
    }

    return true;
  }

  function health() {
    return api("/health");
  }

  window.ImvulaAuth = {
    api: api,
    health: health,
    getToken: getToken,
    getUser: getUser,
    setUser: setUser,
    isLoggedIn: isLoggedIn,
    requireAuth: requireAuth,
    login: login,
    register: register,
    me: me,
    logout: logout,
    clearAuth: clearAuth
  };
})();
