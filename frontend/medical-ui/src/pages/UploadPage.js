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

  // ----------------------------
  // POLLING FUNCTION
  // ----------------------------
  const pollJobStatus = async (jobId) => {
    try {
      const res = await axios.get(`${API_BASE}/status/${jobId}`);
      const data = res.data;

      if (data.status === "done") {
        setProcessing(false);
        navigate(`/summary/${data.report_id}`);
      } 
      else if (data.status === "error") {
        setProcessing(false);
        alert("Processing failed. Please try again.");
      } 
      else {
        // still processing
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

    const formData = new FormData();
    formData.append("file", file);

    try {
      setLoading(true);

      const res = await axios.post(`${API_BASE}/upload`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
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
  // DRAG HANDLERS (UNCHANGED)
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

  // ----------------------------
  // UI (UNCHANGED)
  // ----------------------------
  return (
    <div className="page">
      <h1 className="title">MediDigest : AI Medical Report Summarizer</h1>
      <p className="subtitle">
        Get a summary of medical reports in seconds, read faster and understand better
      </p>

      <div
        className={`upload-card ${dragActive ? "drag-active" : ""}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <div className="upload-icon">
          <img src="/upload-cloud-icon.svg" alt="Upload file" />
        </div>

        <input
          type="file"
          id="fileInput"
          hidden
          onChange={(e) => setFile(e.target.files[0])}
        />

        <label htmlFor="fileInput" className="upload-btn">
          Upload Document
        </label>

        {file && <p className="file-name">{file.name}</p>}

        <p className="drag-text">or Drag file here</p>

        <button
          className="submit-btn"
          onClick={handleUpload}
          disabled={loading}
        >
          {loading ? "Processing..." : "Generate Summary"}
        </button>
      </div>

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
