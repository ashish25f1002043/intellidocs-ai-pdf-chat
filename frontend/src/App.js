import React, { useState, useRef, useEffect } from "react";
import axios from "axios";
import "./App.css";

const API = "http://127.0.0.1:8000";

function App() {
  const [file, setFile] = useState(null);
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef(null);

  // Auto scroll
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Upload PDF
  const uploadPDF = async () => {
    if (!file) return alert("Select PDF first");

    const formData = new FormData();
    formData.append("file", file);

    setLoading(true);

    try {
      await axios.post(`${API}/upload`, formData);
      alert("PDF Uploaded Successfully ✅");
    } catch (err) {
      alert("Upload failed");
    }

    setLoading(false);
  };

  // Ask Question
  const askQuestion = async () => {
    if (!question.trim()) return;

    const userMsg = { role: "user", text: question };
    setMessages((prev) => [...prev, userMsg]);

    setQuestion("");
    setLoading(true);

    try {
      const res = await axios.post(`${API}/ask`, {
        question: question,
      });

      const aiMsg = { role: "ai", text: res.data.answer };

      setMessages((prev) => [...prev, aiMsg]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "ai", text: "Error getting response ❌" },
      ]);
    }

    setLoading(false);
  };

  return (
    <div className="app">

      {/* HEADER */}
      <div className="header">
        <h1>AI PDF Chat Assistant</h1>
      </div>

      {/* UPLOAD SECTION */}
      <div className="uploadCard">
        <input
          type="file"
          accept="application/pdf"
          onChange={(e) => setFile(e.target.files[0])}
        />
        <button onClick={uploadPDF}>
          {loading ? "Uploading..." : "Upload PDF"}
        </button>
      </div>

      {/* CHAT AREA */}
      <div className="chatBox">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`message ${msg.role === "user" ? "user" : "ai"}`}
          >
            {msg.text}
          </div>
        ))}

        {loading && <div className="typing">AI is thinking...</div>}

        <div ref={chatEndRef}></div>
      </div>

      {/* INPUT BOX */}
      <div className="inputBox">
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask anything from your PDF..."
          onKeyDown={(e) => e.key === "Enter" && askQuestion()}
        />

        <button onClick={askQuestion}>Send</button>
      </div>

    </div>
  );
}

export default App;