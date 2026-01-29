import { useState } from "react";
import {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
} from "firebase/auth";
import { auth } from "./firebase";
import "./AuthPage.css";

function AuthPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  // 🔐 LOGIN
  const handleLogin = async (e) => {
    e.preventDefault();

    try {
      await signInWithEmailAndPassword(
        auth,
        email.trim(),
        password.trim()
      );

      window.location.href =
        "http://localhost:3000/d/admwnvn/log-views?orgId=1&from=now-7d&to=now&timezone=browser";
    } catch (err) {
      alert(err.code);
    }
  };

  // 🆕 SIGN UP (PUBLIC)
  const handleSignup = async () => {
    try {
      await createUserWithEmailAndPassword(
        auth,
        email.trim(),
        password.trim()
      );

      alert("Account created successfully. You can now login.");
    } catch (err) {
      alert(err.code);
    }
  };

  return (
    <div className="page">
      <div className="glass-card">
        <h2>Welcome</h2>

        <form onSubmit={handleLogin}>
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />

          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />

          <button type="submit">LOGIN</button>
        </form>

        <p style={{ marginTop: "15px" }}>New user?</p>

        <button
          style={{ background: "#4caf50" }}
          onClick={handleSignup}
        >
          SIGN UP
        </button>
      </div>
    </div>
  );
}

export default AuthPage;
