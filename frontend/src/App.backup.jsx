import { jsPDF } from "jspdf";
import { useState, useEffect } from "react";
import "./App.css";

const API = "http://127.0.0.1:8000";

function App() {
  const [reference, setReference] = useState(null);
  const [test, setTest] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [metrics, setMetrics] = useState(null);
const [metricsError, setMetricsError] = useState("");

const [history, setHistory] = useState(() => {
  try {
    return JSON.parse(
      localStorage.getItem("signguard_history") || "[]"
    );
  } catch {
    return [];
  }
});


useEffect(() => {
  fetch(`${API}/metrics`)
    .then((response) => {
      if (!response.ok) {
        throw new Error("Unable to load model metrics");
      }
      return response.json();
    })
    .then((data) => setMetrics(data))
    .catch((err) => setMetricsError(err.message));
}, []);


  async function verifySignature() {
    if (!reference || !test) {
      setError("Please upload both signatures.");
      return;
    }
    
const allowedTypes = ["image/png", "image/jpeg"];
const maxSize = 5 * 1024 * 1024;

for (const file of [reference, test]) {
  if (!allowedTypes.includes(file.type)) {
    setError("Only PNG, JPG, and JPEG images are allowed.");
    return;
  }

  if (file.size > maxSize) {
    setError("Each signature image must be smaller than 5 MB.");
    return;
  }
}


    setLoading(true);
    setError("");
    setResult(null);

    const formData = new FormData();
    formData.append("reference", reference);
    formData.append("test", test);

    try {
      const response = await fetch(`${API}/predict`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : "Prediction failed"
        );
      }

      setResult(data);
      
const record = {
  id: Date.now(),
  reference: reference.name,
  test: test.name,
  prediction: data.same_writer ? "MATCHED" : "NOT MATCHED",
  same_writer: data.same_writer,
  distance: data.distance,
  date: new Date().toLocaleString()
};

setHistory((previous) => {
  const updated = [record, ...previous].slice(0, 20);
  localStorage.setItem(
    "signguard_history",
    JSON.stringify(updated)
  );
  return updated;
});

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }
  
function downloadReport() {
  if (!result) return;

  const doc = new jsPDF();
  const date = new Date().toLocaleString();

  doc.setFontSize(22);
  doc.setTextColor(20, 41, 75);
  doc.text("SignGuard AI", 20, 25);

  doc.setFontSize(14);
  doc.text("Signature Verification Report", 20, 38);

  doc.setDrawColor(200, 210, 225);
  doc.line(20, 45, 190, 45);

  doc.setFontSize(11);
  doc.setTextColor(40, 50, 65);

  doc.text(`Date: ${date}`, 20, 58);
  doc.text(
    `Reference: ${reference?.name || "Unknown"}`,
    20, 70
  );
  doc.text(
    `Test: ${test?.name || "Unknown"}`,
    20, 82
  );

  doc.setFontSize(16);
  doc.setTextColor(
    result.same_writer ? 22 : 185,
    result.same_writer ? 101 : 28,
    result.same_writer ? 52 : 28
  );

  doc.text(
    result.same_writer ? "MATCHED" : "NOT MATCHED",
    20, 105
  );

  doc.setFontSize(11);
  doc.setTextColor(40, 50, 65);

  doc.text(`Embedding Distance: ${result.distance}`, 20, 122);
  doc.text(`Similarity Score: ${result.similarity_score}`, 20, 134);
  doc.text(`Decision Threshold: ${result.threshold}`, 20, 146);

  doc.setFontSize(10);
  doc.setTextColor(100, 110, 125);
  doc.text(
    "Experimental AI prediction, not proof of authenticity.",
    20, 170
  );

  doc.text(
    "Model: Siamese Convolutional Neural Network",
    20, 182
  );

  doc.save("SignGuard_AI_Verification_Report.pdf");
}

function clearHistory() {
  localStorage.removeItem("signguard_history");
  setHistory([]);
}

function resetSignatures() {
  setReference(null);
  setTest(null);
  setResult(null);
  setError("");

  const inputs = document.querySelectorAll(
    ".upload-card input[type='file']"
  );

  inputs.forEach((input) => {
    input.value = "";
  });
}


  return (
    <div className="app">
      <header className="header">
        <h2>✍ SignGuard AI</h2>
        <span>Deep Learning Signature Verification</span>
      </header>

      <main className="container">
        <section className="hero">
          <h1>AI Signature Forgery Detection</h1>
          <p>
            Compare handwritten signatures using
            a Siamese Convolutional Neural Network.
          </p>
        </section>

        <section className="upload-grid">
          <div className="upload-card">
            <h3>Reference Signature</h3>
            <p>Upload the original signature</p>

            <input
              type="file"
              accept=".png,.jpg,.jpeg"
              onChange={(e) => {
                setReference(e.target.files[0] || null);
                setResult(null);
              }}
            />

            {reference && (
              <img
                src={URL.createObjectURL(reference)}
                alt="Reference signature"
                className="signature-preview"
              />
            )}
          </div>

          <div className="upload-card">
            <h3>Test Signature</h3>
            <p>Upload the signature to verify</p>

            <input
              type="file"
              accept=".png,.jpg,.jpeg"
              onChange={(e) => {
                setTest(e.target.files[0] || null);
                setResult(null);
              }}
            />

            {test && (
              <img
                src={URL.createObjectURL(test)}
                alt="Test signature"
                className="signature-preview"
              />
            )}
          </div>
        </section>

        <button
          className="verify-button"
          onClick={verifySignature}
          disabled={loading}
        >
          {loading ? "Analyzing..." : "Verify Signatures"}
        </button>
        
<button
  className="reset-button"
  onClick={resetSignatures}
  disabled={loading}
>
  Reset Signatures
</button>

{loading && (
  <div className="loading-container">
    <div className="spinner"></div>
    <p>AI is analyzing signature patterns...</p>
  </div>
)}


        {error && <p className="error">{error}</p>}

        {result && (
          <section className="result-card">
            <h2>AI Verification Result</h2>

            
<div className={result.same_writer ? "match" : "mismatch"}>
  <h2>
    {result.same_writer ? "✓ MATCHED" : "✕ NOT MATCHED"}
  </h2>

  <p>
    {result.same_writer
      ? "Likely Same Writer"
      : "Possible Forgery / Different Writer"}
  </p>
</div>


            <div className="metrics">
              <div>
                <p>Embedding Distance</p>
                <strong>{result.distance}</strong>
              </div>

              <div>
                <p>Similarity Score</p>
                <strong>{result.similarity_score}</strong>
              </div>

              <div>
                <p>Decision Threshold</p>
                <strong>{result.threshold}</strong>
              </div>
            </div>

            <p>{result.message}</p>
            <button
  className="download-button"
  onClick={downloadReport}
>
  Download PDF Report
</button>
          </section>
        )}
        
<section className="performance-section">
  <h2>Model Performance Dashboard</h2>
  <p>Evaluation on unseen CEDAR test writers</p>

  {metricsError && <p className="error">{metricsError}</p>}

  {metrics && (
    <>
      <div className="performance-grid">
        {[
          ["Accuracy", metrics.accuracy],
          ["Precision", metrics.precision],
          ["Recall", metrics.recall],
          ["F1 Score", metrics.f1_score],
          ["ROC-AUC", metrics.roc_auc]
        ].map(([name, value]) => (
          <div className="performance-card" key={name}>
            <span>{name}</span>
            <h2>{(value * 100).toFixed(2)}%</h2>
          </div>
        ))}
      </div>

      <h3>Confusion Matrix</h3>

      <div className="confusion-grid">
        {metrics.confusion_matrix.flat().map((value, index) => (
          <div key={index}>{value}</div>
        ))}
      </div>

      <p>
        Test Pairs: {metrics.test_pairs} |
        Test Writers: {metrics.test_writers}
      </p>
    </>
  )}
</section>

<section className="history-section">
  <div className="history-header">
    <h2>Signature Comparison History</h2>

    <button
      className="clear-button"
      onClick={clearHistory}
      disabled={history.length === 0}
    >
      Clear History
    </button>
  </div>

  {history.length === 0 ? (
    <p>No comparisons recorded yet.</p>
  ) : (
    <div className="history-scroll">
      <table className="history-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Reference</th>
            <th>Test</th>
            <th>Result</th>
            <th>Distance</th>
          </tr>
        </thead>

        <tbody>
          {history.map((item) => (
            <tr key={item.id}>
              <td>{item.date}</td>
              <td>{item.reference}</td>
              <td>{item.test}</td>
              <td>
                <span
                  className={
                    item.same_writer
                      ? "history-match"
                      : "history-mismatch"
                  }
                >
                  {item.prediction}
                </span>
              </td>
              <td>{item.distance}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )}
</section>



        <section className="about">
          <h2>How SignGuard AI Works</h2>
          <p>
            Upload → Image Preprocessing → Siamese CNN
            → Feature Comparison → Prediction
          </p>
        </section>
      </main>

      <footer>
        SignGuard AI | Deep Learning Project
      </footer>
    </div>
  );
}

export default App;
