import React, { useState } from "react";
import axios from "axios";
import Lottie from "lottie-react";
import aiLoader from "../assets/gradient loader 01.json";
import { useNavigate } from "react-router-dom";
import "./UploadPage.css";

const API_BASE = process.env.REACT_APP_API_URL;

function UploadPage() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [processing, setProcessing] = useState(false);
  const navigate = useNavigate();
  const token = localStorage.getItem("token");
  const isLoggedIn = Boolean(token);

  // ----------------------------
  // POLLING FUNCTION
  // ----------------------------
  const pollJobStatus = async (jobId) => {
    try {
      const res = await axios.get(`${API_BASE}/status/${jobId}`);
      const data = res.data;

      if (data.status === "done") {
        setProcessing(false);
        navigate(`/public/report/${data.public_id}`);
      } else if (data.status === "error") {
        setProcessing(false);
        alert("Processing failed. Please try again.");
      } else {
        setTimeout(() => pollJobStatus(jobId), 3000);
      }
    } catch (err) {
      console.error(err);
      setTimeout(() => pollJobStatus(jobId), 5000);
    }
  };

  // ----------------------------
  // UPLOAD HANDLER
  // ----------------------------
  const handleUpload = async () => {
    if (!file) {
      alert("Please upload a valid report first.");
      return;
    }

    const ALLOWED_TYPES = ["application/pdf", "image/png", "image/jpeg"];

    if (!ALLOWED_TYPES.includes(file.type)) {
      alert("Please upload a PDF, PNG, or JPG/JPEG file only.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      setLoading(true);

      const res = await axios.post(`${API_BASE}/upload`, formData, {
        headers:  { "Content-Type": "multipart/form-data" },
      });

      const jobId = res.data.job_id;

      setProcessing(true);
      pollJobStatus(jobId);
    } catch (err) {
      console.error(err);
      alert("Upload failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  // ----------------------------
  // DRAG HANDLERS
  // ----------------------------
  const handleDragOver = (e) => {
    e.preventDefault();
    setDragActive(true);
  };

  const handleDragLeave = () => {
    setDragActive(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setFile(e.dataTransfer.files[0]);
      e.dataTransfer.clearData();
    }
  };

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
    }
  };

  // ----------------------------
  // UI
  // ----------------------------
  return (
    <div className="page">
      {/* Navigation Bar */}
      <nav className="navbar">
        <div className="nav-brand">
            <img src="/logo.png" className="logo" alt="MediDigest Logo"/>
          <span className="brand-name">MediDigest</span>
        </div>

        <div className="nav-actions">
          {! isLoggedIn ?  (
            <>
              <button
                className="nav-btn outline"
                onClick={() => navigate("/login")}
              >
                Login
              </button>
              <button
                className="nav-btn outline"
                onClick={() => navigate("/signup")}
              >
                Sign up
              </button>
            </>
          ) : (
            <>
              <button
                className="nav-btn outline"
                onClick={() => navigate("/history")}
              >
                History
              </button>
              <button
                className="nav-btn outline"
                onClick={() => {
                  localStorage.removeItem("token");
                  navigate("/");
                }}
              >
                Logout
              </button>
            </>
          )}
        </div>
      </nav>

      {/* Hero Section */}
      <div className="hero-section">
      <h1 class="hero-title">
        MediDigest : AI Medical Report Summarizer
      </h1>
        <p className="hero-subtitle">
          Get a summary of medical reports in seconds, read faster and understand better
        </p>
      </div>

      {/* Upload Card */}
      <div
        className={`upload-card ${dragActive ? "drag-active" : ""}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        {/* Cloud Upload Icon */}
        <div className="upload-icon">
          <img src="/upload-cloud-icon.svg" alt="Upload file" />
        </div>

        {/* Upload Button */}
        <label className="upload-btn">
          Upload Document
          <input
            type="file"
            accept=".pdf,.png,.jpg,.jpeg"
            onChange={handleFileSelect}
            hidden
          />
        </label>

        {/* Drag Text */}
        <p className="drag-text">or Drag file here</p>

        {/* File Name Display */}
        {file && <p className="file-name">{file.name}</p>}

        {/* Generate Summary Button */}
        <button
          className="submit-btn"
          onClick={handleUpload}
          disabled={loading || ! file}
        >
          {loading ? "Uploading..." : "Generate Summary"}
        </button>
      </div>

      {/* Processing Overlay */}
      {processing && (
        <div className="processing-overlay">
          <div className="processing-content">
            <Lottie animationData={aiLoader} loop />
            <p className="processing-text">
              Generating a summary typically takes about 1 minute.
              <br />
              Please don’t close this window.
            </p>
            <div className="progress-bar">
              <div className="progress-line" />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default UploadPage;