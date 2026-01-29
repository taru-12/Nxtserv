import React from "react";
import "./Login.css";

export default function Login() {
  return (
    <div className="login-wrapper">
      <div className="login-glass">
        <h1 className="brand">SIEM<span>Guard</span></h1>
        <p className="subtitle">Secure Log Intelligence Platform</p>

        <div className="input-group">
          <input type="text" required />
          <label>Username</label>
        </div>

        <div className="input-group">
          <input type="password" required />
          <label>Password</label>
        </div>

        <button className="login-btn">Access Dashboard</button>

        <p className="footer-text">
          Monitoring • Alerts • Analytics
        </p>
      </div>
    </div>
  );
}
