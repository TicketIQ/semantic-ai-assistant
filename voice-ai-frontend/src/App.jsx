import { useState, useRef } from "react";

export default function App() {
  const [text, setText] = useState("");
  const [response, setResponse] = useState("");

  const recognitionRef = useRef(null);

  const startVoice = () => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert("Speech API not supported in this browser");
      return;
    }

    const recognition = new SpeechRecognition();

    // ✅ FIXED SETTINGS (important for no-speech issue)
    recognition.lang = "en-US";
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;

    let finalText = "";

    recognition.onstart = () => {
      console.log("🟢 Listening started...");
    };

    recognition.onresult = (event) => {
      let interimText = "";

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;

        if (event.results[i].isFinal) {
          finalText += transcript + " ";
        } else {
          interimText += transcript;
        }
      }

      const fullText = finalText + interimText;

      console.log("🎤 LIVE:", fullText);
      setText(fullText);
    };

    recognition.onerror = (event) => {
      console.log("❌ Speech error:", event.error);
    };

    recognition.onend = async () => {
      console.log("⛔ Speech stopped");

      const cleaned = finalText.trim();

      if (!cleaned) {
        console.log("⚠️ No speech detected (ignored)");
        return;
      }

      try {
        const res = await fetch("http://127.0.0.1:8001/process", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ text: cleaned }),
        });

        const data = await res.json();

        console.log("📦 Backend response:", data);

        setResponse(data.response);
      } catch (err) {
        console.error("❌ Backend error:", err);
      }

      finalText = "";
    };

    recognition.start();
    recognitionRef.current = recognition;
  };

  const stopVoice = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      recognitionRef.current = null;
    }
  };

  return (
    <div style={{ textAlign: "center", marginTop: "100px" }}>
      <h1>🎤 Voice AI Assistant</h1>

      <button onClick={startVoice}>Start 🎤</button>

      <button onClick={stopVoice} style={{ marginLeft: "10px" }}>
        Stop ⛔
      </button>

      <h3>🗣️ You said:</h3>

      <input
        value={text}
        readOnly
        style={{
          width: "420px",
          padding: "10px",
          fontSize: "16px",
        }}
      />

      <h3>🤖 Response:</h3>
      <p>{response}</p>
    </div>
  );
}