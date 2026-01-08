import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import "./LoginPage.css";

const API_BASE = process.env.REACT_APP_API_URL;

function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
  
    if (!email || !password) {
      alert("Please fill all fields");
      return;
    }
  
    try {
      const res = await axios.post(`${API_BASE}/auth/login`, {
        email,
        password,
      });
  
      const token = res.data.token;
      localStorage.setItem("token", token);
  
      // Check if there's a pending save report
      const pending = localStorage.getItem("pendingSaveReport");
  
      if (pending) {
        const { reportId } = JSON.parse(pending);
        
        // Save the report to user's history
        try {
          await axios.post(
            `${API_BASE}/report/${reportId}/attach`,
            {},
            {
              headers: {
                Authorization: `Bearer ${token}`,
              },
            }
          );
  
          // Clean up the pending save
          localStorage.removeItem("pendingSaveReport");
          
          // Show success message and redirect to history
          alert("Summary saved to your history!");
          navigate("/history");
          return;
        } catch (err) {
          console.error("Failed to save pending report:", err);
          // Even if save fails, clean up and continue
          localStorage.removeItem("pendingSaveReport");
        }
      }
  
      // Normal login flow - redirect to home
      navigate("/");
      
    } catch (err) {
      alert("Invalid credentials");
    }
  };

  return (
    <div className="login-container">

      <div className="login-header">
        <h1 className="logo-text">
          MediDigest :  AI Medical Report Summarizer
        </h1>
      </div>

      <div className="login-card">
        <h2 className="login-title">Sign in</h2>

        <form onSubmit={handleLogin} className="login-form">
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="login-input"
          />

          <div className="password-input-wrapper">
            <input
              type={showPassword ? "text" : "password"}
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="login-input"
            />
            <button
              type="button"
              className="password-toggle"
              onClick={() => setShowPassword(!showPassword)}
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

          <button type="submit" className="login-button">
            Sign in
          </button>
        </form>

        <p className="signup-prompt">
          Don't have an account?{" "}
          <span className="signup-link" onClick={() => navigate("/signup")}>
            Sign up
          </span>
        </p>
      </div>
    </div>
  );
}

export default LoginPage;