
import { useState } from "react";
import App from "./App";
import Login from "./pages/Login";
import Register from "./pages/Register";

const API_URL = "http://127.0.0.1:8001";

function AuthApp() {
  const [page, setPage] = useState("login");
  const [token, setToken] = useState(() => {
  const savedToken = sessionStorage.getItem("signguard_token");

  if (!savedToken) return null;

  try {
    const payload = JSON.parse(
      atob(savedToken.split(".")[1].replace(/-/g, "+").replace(/_/g, "/"))
    );

    if (typeof payload.exp !== "number" ||
        payload.exp * 1000 <= Date.now()) {
      sessionStorage.removeItem("signguard_token");
      return null;
    }

    return savedToken;
  } catch {
    sessionStorage.removeItem("signguard_token");
    return null;
  }
});
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function authenticate(endpoint, details) {
    setError("");
    setLoading(true);

    try {
      const response = await fetch(
        `${API_URL}/auth/${endpoint}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(details),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : "Please check your details."
        );
      }
      sessionStorage.setItem("signguard_token", data.access_token);

      setToken(data.access_token);
      setPage("dashboard");
    } catch (err) {
      setError(err.message || "Unable to connect to backend.");
    } finally {
      setLoading(false);
    }
  }
  function handleLogout() {
  sessionStorage.removeItem("signguard_token");
  setToken(null);
  setError("");
  setPage("login");
}

  

if (token) {
  const navigateTo = (section) => {
    const selectors = {
      dashboard: ".app, .container, main",
      verify: ".upload-section, .upload-container, .verification-section",
      analytics: ".metrics-section, .performance-section",
      history: ".history-section",
    };

    const element = document.querySelector(selectors[section]);

    if (element) {
      element.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }
  };

  return (
    <div className="premium-layout">
      <aside className="premium-sidebar">
        <div className="sidebar-brand">✦ SignGuard AI</div>

        <p className="sidebar-label">WORKSPACE</p>

        <nav className="sidebar-navigation">
          <button onClick={() => navigateTo("dashboard")}>
            ◈ Dashboard
          </button>

          <button onClick={() => navigateTo("verify")}>
            ◉ Verify Signature
          </button>

          <button onClick={() => navigateTo("analytics")}>
            ▥ Analytics
          </button>

          <button onClick={() => navigateTo("history")}>
            ◷ History
          </button>
        </nav>

        <div className="sidebar-bottom">
          <span>● AI System Online</span>

          <button
            className="sidebar-logout"
            onClick={handleLogout}
          >
            ↪ Logout
          </button>
        </div>
      </aside>

      <main className="premium-content">
        <App />
      </main>
    </div>
  );
}


  

  return (
    <>
      {page === "register" ? (
        <Register
          onSwitch={() => {
            setError("");
            setPage("login");
          }}
          onRegister={(details) =>
            authenticate("register", details)
          }
        />
      ) : (
        <Login
          onSwitch={() => {
            setError("");
            setPage("register");
          }}
          onLogin={(details) =>
            authenticate("login", details)
          }
        />
      )}

      {(error || loading) && (
        <div className="auth-feedback" role="status">
          {loading ? "Please wait..." : error}
        </div>
      )}
    </>
  );
}

export default AuthApp;
