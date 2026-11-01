
import { useState } from "react";
import "../styles/Auth.css";

function Register({ onSwitch, onRegister }) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");

  function handleSubmit(e) {
    e.preventDefault();
    setError("");

    if (password.length < 8) {
      setError("Password must contain at least 8 characters.");
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    onRegister({ name, email, password });
  }

  return (
    <div className="auth-page">
      <div className="auth-brand">
        <div className="auth-logo">✦ SignGuard AI</div>
        <h1>
          Your Security.
          <span> Our Intelligence.</span>
        </h1>
        <p>
          Create your account and explore
          AI-powered signature verification.
        </p>

        <div className="auth-feature">
          ✓ Secure account management
        </div>
        <div className="auth-feature">
          ✓ Signature verification dashboard
        </div>
        <div className="auth-feature">
          ✓ Downloadable analysis reports
        </div>
      </div>

      <div className="auth-card">
        <div className="auth-icon">✦</div>
        <h2>Create Account</h2>
        <p className="auth-subtitle">
          Get started with SignGuard AI
        </p>

        <form onSubmit={handleSubmit}>
          <label>Full Name</label>
          <input
            type="text"
            placeholder="Enter your full name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />

          <label>Email Address</label>
          <input
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />

          <label>Password</label>
          <input
            type="password"
            placeholder="Minimum 8 characters"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />

          <label>Confirm Password</label>
          <input
            type="password"
            placeholder="Re-enter your password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
          />

          {error && <p className="auth-error">{error}</p>}

          <button className="auth-submit" type="submit">
            Create Account →
          </button>
        </form>

        <p className="auth-switch">
          Already have an account?{" "}
          <button type="button" onClick={onSwitch}>
            Sign In
          </button>
        </p>
      </div>
    </div>
  );
}

export default Register;
