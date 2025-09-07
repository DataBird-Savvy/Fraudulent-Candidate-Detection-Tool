"use client";

import { useState } from "react";
import { FaCheckCircle, FaExclamationTriangle, FaFileAlt } from "react-icons/fa";
import "./HomePage.css"; 

const StatusBadge = ({ status }) => {
  const isSuspicious = status === "suspicious";
  const Icon = isSuspicious ? FaExclamationTriangle : FaCheckCircle;

  return (
    <div className={`status-badge ${isSuspicious ? "suspicious" : "safe"}`}>
      <Icon className="status-icon" />
      <span className="status-text">{status}</span>
    </div>
  );
};

export default function HomePage() {
  const [file, setFile] = useState(null);
  const [jd, setJD] = useState("");
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleFileChange = (e) => setFile(e.target.files[0]);
  const handleJDChange = (e) => setJD(e.target.value);

  const handleSubmit = async () => {
    if (!file) return alert("Please upload a resume.");
    setLoading(true);

    const formData = new FormData();
    formData.append("file", file);
    if (jd) formData.append("jd", jd);

    try {
      const res = await fetch("http://localhost:8000/analyze", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) throw new Error("Failed to analyze resume");

      const data = await res.json();
      setReport(data.report);
    } catch (err) {
      console.error(err);
      alert("Error analyzing resume.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <h1>Fraudulent Candidate Detection</h1>

      {/* Upload Form */}
      <div className="form-card">
        <div className="form-group">
          <label>Upload Resume (PDF, DOCX)</label>
          <input type="file" onChange={handleFileChange} />
        </div>

        <div className="form-group">
          <label>Job Description (Optional)</label>
          <textarea
            rows={5}
            value={jd}
            onChange={handleJDChange}
            placeholder="Paste job description here..."
          />
        </div>

        <button onClick={handleSubmit} disabled={loading}>
          {loading ? "Analyzing..." : "Analyze Resume"}
        </button>
      </div>

      {/* Report Display */}
      {report && (
        <div className="report-section">
          <h2>Fraud Report</h2>

          {/* Experience Check */}
          <div className="report-block">
            <h3>Experience Check</h3>
            {report.fraud_indicators.map((f, idx) => (
              <div key={idx} className="report-card">
                <StatusBadge status={f.status} />
                <p>
                  <strong>Reasoning:</strong> {f.reasoning}
                </p>
                {f.flags && (
                  <p>
                    <strong>Flags:</strong> {f.flags.join(", ")}
                  </p>
                )}
              </div>
            ))}
          </div>

          {/* Plagiarism Summary */}
          <div className="report-block">
            <h3>Plagiarism Summary</h3>
            {report.plagiarism_summary.map((p, idx) => (
              <div key={idx} className="plagiarism-card">
                <FaFileAlt className="plagiarism-icon" />
                <div>
                  <p>
                    <strong>File:</strong> {p.source_file}
                  </p>
                  <p>
                    <strong>Score:</strong> {p.score}
                  </p>
                </div>
              </div>
            ))}
          </div>

          {/* Resume vs JD Similarity */}
          <div className="report-card similarity-card">
            <h3>Resume vs JD Similarity</h3>
            <p>{report.resume_vs_jd_similarity}</p>
          </div>

          {/* Education Anomalies */}
          {report.education_anomalies && report.education_anomalies.length > 0 && (
            <div className="report-card education-card">
              <h3>Education Anomalies</h3>
              <ul>
                {report.education_anomalies.map((e, idx) => (
                  <li key={idx}>{e}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Final Recommendation */}
          <div className="report-card final-card">
            <h3>Final Recommendation</h3>
            <p>{report.final_recommendation}</p>
          </div>
        </div>
      )}
    </div>
  );
}
