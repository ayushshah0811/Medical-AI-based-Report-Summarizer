import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import "./SignupPage.css";

const API_BASE = process.env.REACT_APP_API_URL;

function SignupPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSignup = async (e) => {
    e.preventDefault();
  
    if (!email || !password || !confirm) {
      alert("Please fill all fields");
      return;
    }
  
    if (password !== confirm) {
      alert("Passwords do not match");
      return;
    }

    setLoading(true);
  
    try {
      // Step 1: Create the account
      await axios.post(`${API_BASE}/auth/signup`, {
        email,
        password,
      });

      // Step 2: Immediately login with the same credentials
      const loginRes = await axios.post(`${API_BASE}/auth/login`, {
        email,
        password,
      });

      const token = loginRes.data.token;
      localStorage.setItem("token", token);

      // Step 3: Check if there's a pending report to save
      const pending = localStorage.getItem("pendingSaveReport");

      if (pending) {
        const { reportId } = JSON.parse(pending);
        
        try {
          // Save the pending report to user's history
          await axios.post(
            `${API_BASE}/report/${reportId}/attach`,
            {},
            {
              headers: {
                Authorization: `Bearer ${token}`,
              },
            }
          );

          // Clean up
          localStorage.removeItem("pendingSaveReport");
          
          alert("Account created and summary saved to your history!");
          navigate("/history");
          return;
        } catch (err) {
          console.error("Failed to save pending report:", err);
          localStorage.removeItem("pendingSaveReport");
          // Continue with normal flow even if save fails
        }
      }

      // Normal signup flow (no pending report)
      alert("Account created successfully!");
      navigate("/");
  
    } catch (err) {
      console.error(err);
      alert("Signup failed. Email might already be registered.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="signup-container">
      <div className="signup-header">
        <h1 className="logo-text">
          MediDigest :  AI Medical Report Summarizer
        </h1>
      </div>

      <div className="signup-card">
        <h2 className="signup-title">Create account</h2>

        <form onSubmit={handleSignup} className="signup-form">
          <div className="input-wrapper">
            <input
              type="email"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="signup-input"
              disabled={loading}
            />
          </div>

          <div className="password-input-wrapper">
            <input
              type={showPassword ? "text" : "password"}
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="signup-input"
              disabled={loading}
            />
            <button
              type="button"
              className="password-toggle"
              onClick={() => setShowPassword(!showPassword)}
              disabled={loading}
            >
              {showPassword ? (
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
                  <line x1="1" y1="1" x2="23" y2="23"/>
                </svg>
              ) : (
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                  <circle cx="12" cy="12" r="3"/>
                </svg>
              )}
            </button>
          </div>

          <div className="password-input-wrapper">
            <input
              type={showConfirm ? "text" : "password"}
              placeholder="Confirm password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              className="signup-input"
              disabled={loading}
            />
            <button
              type="button"
              className="password-toggle"
              onClick={() => setShowConfirm(!showConfirm)}
              disabled={loading}
            >
              {showConfirm ? (
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
                  <line x1="1" y1="1" x2="23" y2="23"/>
                </svg>
              ) : (
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                  <circle cx="12" cy="12" r="3"/>
                </svg>
              )}
            </button>
          </div>

          <button type="submit" className="signup-button" disabled={loading}>
            {loading ? "Creating account..." : "Sign up"}
          </button>
        </form>

        <p className="signin-prompt">
          Already have an account?{" "}
          <span className="signin-link" onClick={() => navigate("/login")}>
            Sign in
          </span>
        </p>
      </div>
    </div>
  );
}

export default SignupPage;