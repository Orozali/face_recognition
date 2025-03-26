import React, { useEffect, useRef, useState } from "react";

const FaceRecognition = () => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const ws = useRef(null);
  
  const [faces, setFaces] = useState([]);
  
  useEffect(() => {
    // Access the user's camera
    navigator.mediaDevices.getUserMedia({ video: true }).then((stream) => {
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }

      // Open WebSocket connection
      ws.current = new WebSocket("ws://localhost:8001/ws");

      ws.current.onopen = () => {
        console.log("WebSocket Connected!");
        sendFrame(); // Start sending frames immediately after WebSocket is open
      };

      ws.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log("Received Data:", data); // Debug WebSocket response

        if (data.students) {
          const detectedFaces = data.students.map((student) => {
            const [x, y, w, h] = student.bbox;
            return {
              x,
              y,
              w: w - x,
              h: h - y,
              name: `${student.name} ${student.surname}`,
              student_id: student.student_id,
            };
          });
          setFaces(detectedFaces);
        }
      };

      ws.current.onerror = (error) => console.error("WebSocket Error:", error);

      // Function to send frames every 100ms
      const sendFrame = () => {
        if (ws.current.readyState === WebSocket.OPEN && videoRef.current) {
          const canvas = document.createElement("canvas");
          const ctx = canvas.getContext("2d");

          canvas.width = videoRef.current.videoWidth;
          canvas.height = videoRef.current.videoHeight;
          ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);

          canvas.toBlob((blob) => {
            if (blob) {
              ws.current.send(blob); // Send the frame to WebSocket
              console.log("Frame sent!"); // Debug if frames are being sent
            }
          }, "image/jpeg");
        }

        setTimeout(sendFrame, 100); // Continue sending frames every 100ms
      };

      // Clean up WebSocket connection on component unmount
      return () => {
        if (ws.current) ws.current.close();
      };
    });
  }, []); // Run only once on component mount

  // Drawing boxes on detected faces
  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");

    const drawBoxes = () => {
      if (!canvas || !ctx || !videoRef.current) return;

      canvas.width = videoRef.current.videoWidth;
      canvas.height = videoRef.current.videoHeight;
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      faces.forEach(({ x, y, w, h, name }) => {
        const isUnknown = name.trim().toLowerCase() === "unknown unknown";
        const displayName = isUnknown ? "Unknown" : name;

        ctx.strokeStyle = isUnknown ? "red" : "green";
        ctx.lineWidth = 2;
        ctx.font = "18px Arial";
        ctx.fillStyle = isUnknown ? "red" : "green";

        ctx.strokeRect(x, y, w, h);
        ctx.fillText(displayName, x + 5, y - 5);
      });

      requestAnimationFrame(drawBoxes);
    };

    drawBoxes();
  }, [faces]);

  return (
    <div style={{ position: "relative" }}>
      <video ref={videoRef} autoPlay playsInline style={{ width: "100%" }} />
      <canvas
        ref={canvasRef}
        style={{ position: "absolute", top: 0, left: 0, width: "100%" }}
      />
    </div>
  );
};

export default FaceRecognition;
