import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AgentsPage } from "./pages/Agents";
import { BoardPage } from "./pages/Board";
import { AgentChatPage } from "./pages/Chat";
import { Projects } from "./pages/Projects";

function App() {
  return (
    <BrowserRouter>
      <div className="mx-auto max-w-5xl min-h-screen bg-[#0f1419] px-6 py-4 pb-12 font-sans text-[#e8eaed]">
        <header className="mb-6 flex items-baseline gap-3 border-b border-[#2a3441] pb-3">
          <span className="text-xl font-bold tracking-tight">agentctl</span>
          <span className="text-xs font-medium uppercase text-sky-300">
            gateway
          </span>
        </header>
        <main>
          <Routes>
            <Route path="/" element={<Projects />} />
            <Route path="/board/:projectId" element={<BoardPage />} />
            <Route path="/agents/:projectId" element={<AgentsPage />} />
            <Route
              path="/chat/:projectId/:agentId"
              element={<AgentChatPage />}
            />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
