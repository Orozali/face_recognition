import { Routes, Route, Router } from "react-router-dom";
import Homepage from "./pages/Homepage"; 

function App() {
  return (
    <div>
      <Routes>
        {/* Public Routes */}
        <Route path="/" element={<Homepage />} />
      </Routes>
    </div>
  );
}

export default App;
