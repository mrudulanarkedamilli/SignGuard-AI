
import { useState } from "react";
import "../styles/Auth.css";

function Login({ onSwitch, onLogin }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  function handleSubmit(e) {
    e.preventDefault();
    onLogin({ email, password });
  }

  return (
    <div className="auth-page">
      <div className="auth-brand">
        <div className="auth-logo">✦ SignGuard AI</div>
        <h1>
          Intelligent Signature
          <span> Verification.</span>
        </h1>
        <p>
          Secure document workflows powered by
          deep learning and signature analysis.
        </p>

        <div className="auth-feature">
          ✓ AI-powered signature comparison
        </div>
        <div className="auth-feature">
          ✓ Detailed verification reports
        </div>
        <div className="auth-feature">
          ✓ Advanced model analytics
        </div>
      </div>

      <div className="auth-card">
        <div className="auth-icon">✦</div>
        <h2>Welcome Back</h2>
        <p className="auth-subtitle">
          Sign in to your SignGuard AI account
        </p>

        <form onSubmit={handleSubmit}>
          <label>Email Address</label>
          <input
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />

          <label>Password</label>
          <div className="auth-password">
            <input
              type={showPassword ? "text" : "password"}
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
            >
              {showPassword ? "Hide" : "Show"}
            </button>
          </div>

          <button className="auth-submit" type="submit">
            Sign In →
          </button>
        </form>

        <p className="auth-switch">
          Don't have an account?{" "}
          <button type="button" onClick={onSwitch}>
            Create Account
          </button>
        </p>
      </div>
    </div>
  );
}

export default Login;
