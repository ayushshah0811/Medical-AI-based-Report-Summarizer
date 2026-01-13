import React, { useEffect, useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import "./HistoryPage.css"

const API_BASE = process.env.REACT_APP_API_URL;

function HistoryPage() {
  const [reports, setReports] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem("token");

    if (!token) {
      navigate("/login");
      return;
    }

    axios
      .get(`${API_BASE}/my-reports`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
      .then((res) => setReports(res.data))
      .catch(() => {
        alert("Failed to load history");
      });
  }, [navigate]);

  return (
    <div className="history-page">
      <h2>Your Saved Summaries</h2>

      {reports.length === 0 && (
        <p>No saved summaries yet.</p>
      )}

      <ul className="history-list">
        {reports.map((r) => (
          <li
            key={r.id}
            onClick={() => navigate(`/report/${r.id}`)}
            style={{ cursor: "pointer" }}
          >
            <strong>{r.filename}</strong>
            <br />
            <small>{new Date(r.created_at).toISOString()}</small>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default HistoryPage;
