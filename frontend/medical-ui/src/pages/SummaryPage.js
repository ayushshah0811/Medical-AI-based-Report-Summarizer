import React, { useEffect, useState } from "react";
import { useNavigate,useParams } from "react-router-dom";
import axios from "axios";
import ReactMarkdown from "react-markdown";
import html2pdf from "html2pdf.js"
import remarkGfm from "remark-gfm";
import "./SummaryPage.css";

const API_BASE = process.env.REACT_APP_API_URL;

function SummaryPage() {
  const params = useParams();
  const publicId = params.publicId;
  const reportId = params.reportId;
  const isPublic = Boolean(publicId);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchReport = async () => {
      try {
        // 🔓 PUBLIC MODE — NEVER REQUIRE LOGIN
        if (isPublic) {
          const res = await axios.get(
            `${API_BASE}/public/report/${publicId}`
          );
          setReport(res.data);
          return;
        }
  
        // 🔒 PRIVATE MODE — LOGIN REQUIRED
        const token = localStorage.getItem("token");
        if (!token) {
          navigate("/login");
          return;
        }
  
        const res = await axios.get(
          `${API_BASE}/report/${reportId}`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );
        setReport(res.data);
  
      } catch (err) {
        console.error(err);
        alert("Unable to load summary");
      } finally {
        setLoading(false);
      }
    };
  
    fetchReport();
  }, [isPublic, publicId, reportId, navigate]);

  if (loading) {
    return <div className="summary-loading">Loading report...</div>;
  }

  if (!report) {
    return <div className="summary-loading">Report not found</div>;
  }

  const handleDownload = () => {
    const element = document.getElementById("summary-card");
  
    const options = {
      margin: 10,
      filename: "medical-report-summary.pdf",
      image: { type: "jpeg", quality: 1 },
      html2canvas: { scale: 3 },
      jsPDF: { unit: "mm", format: "a3", orientation: "portrait" }
    };
  
    html2pdf().set(options).from(element).save();
  };

  const handleSave = async () => {
    if (!isPublic) return;
  
    const token = localStorage.getItem("token");
    if (!token) {
      // Store the intent to save this report
      localStorage.setItem("pendingSaveReport", JSON.stringify({
        reportId: report.id,
        publicId: publicId
      }));
      
      // Redirect to login
      navigate("/login");
      return;
    }
  
    try {
      await axios.post(
        `${API_BASE}/report/${report.id}/attach`,
        {},
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
  
      alert("Summary saved to your history!");
      navigate("/history");
    } catch (err) {
      console.error(err);
      alert("Failed to save summary");
    }
  };
  

  return (
    <div className="summary-page">
      <div id="summary-card" className="summary-card">
        <h1 className="report-title">
          Medical Report Summary
        </h1>

        <div className="report-meta">
          <span><strong>File:</strong> {report.filename}</span>
          <span><strong>Date:</strong> {new Date(report.created_at).toLocaleDateString()}</span>
        </div>

        <hr />

        <div className="summary-content">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {report.summary}
        </ReactMarkdown>
        </div>
      </div>

        <div className="download-panel">
        {publicId && (
        <button onClick={handleSave}>
          Save this summary
        </button>
        )}

        <button
        className="download-btn"
        onClick={handleDownload}
        disabled={!report.summary}>
        ⬇ Download
        </button>
        </div>    
    </div>
  );
}

export default SummaryPage;
