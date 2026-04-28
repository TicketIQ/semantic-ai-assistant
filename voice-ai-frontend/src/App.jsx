import { useState, useRef } from "react";

export default function App() {
  const [text, setText] = useState("");
  const [response, setResponse] = useState("");
  const recognitionRef = useRef(null);

  const startVoice = () => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert("Speech Recognition not supported in this browser");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.continuous = false;

    recognition.onresult = async (event) => {
      const transcript = event.results[0][0].transcript;
      setText(transcript);

      // call backend
      const res = await fetch("http://127.0.0.1:8001/process", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ text: transcript }),
      });

      const data = await res.json();
      setResponse(data.response);
    };

    recognition.onend = () => {
      console.log("Voice stopped");
    };

    recognitionRef.current = recognition;
    recognition.start();
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

      <button
        onClick={startVoice}
        style={{
          fontSize: "18px",
          padding: "10px 20px",
          marginRight: "10px",
          cursor: "pointer",
        }}
      >
        Start 🎤
      </button>

      <button
        onClick={stopVoice}
        style={{
          fontSize: "18px",
          padding: "10px 20px",
          cursor: "pointer",
          backgroundColor: "red",
          color: "white",
        }}
      >
        Stop ⛔
      </button>

      <h3>🗣️ You said:</h3>
      <p>{text}</p>

      <h3>🤖 Response:</h3>
      <p>{response}</p>
    </div>
  );
}