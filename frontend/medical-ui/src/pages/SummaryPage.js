import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import axios from "axios";
import ReactMarkdown from "react-markdown";
import html2pdf from "html2pdf.js"
import remarkGfm from "remark-gfm";
import "./SummaryPage.css";

const API_BASE = process.env.REACT_APP_API_URL;

function SummaryPage() {
  const { id } = useParams();
  const [report, setReport] = useState(null);

  useEffect(() => {
    axios.get(`${API_BASE}/report/${id}`)
      .then(res => setReport(res.data))
      .catch(err => console.error(err));
  }, [id]);

  if (!report) {
    return <div className="summary-loading">Loading report...</div>;
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
