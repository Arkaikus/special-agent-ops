import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { BoardPage } from "./pages/Board";
import { Projects } from "./pages/Projects";
import "./App.css";

function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <header className="header">
          <span className="logo">agentctl</span>
          <span className="tag">gateway</span>
        </header>
        <main>
          <Routes>
            <Route path="/" element={<Projects />} />
            <Route path="/board/:projectId" element={<BoardPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
