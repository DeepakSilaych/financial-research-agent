import React, { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { MainLayout } from "./components/layout/MainLayout";
import { HomePage } from "./pages/HomePage";
import { ChatPage } from "./pages/ChatPage";
import { UploadPage } from "./pages/UploadPage";
import { ReportsPage } from "./pages/ReportsPage";
import { LoginPage } from "./pages/LoginPage";
import { RegisterPage } from "./pages/RegisterPage";
import { WorkspacePage } from "./pages/WorkspacePage";
import { CreateWorkspacePage } from "./pages/CreateWorkspacePage";
import { ToastProvider } from "./components/ui/use-toast";

function ProtectedRoute({ children }) {
  const user = JSON.parse(localStorage.getItem("user") || "null");
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    const user = JSON.parse(localStorage.getItem("user") || "null");
    setIsLoggedIn(!!user);
  }, []);

  const logout = () => {
    localStorage.removeItem("user");
    setIsLoggedIn(false);
  };

  return (
    <ToastProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<RegisterPage />} />
          <Route path="/register" element={<Navigate to="/signup" replace />} />

          <Route path="/*" element={
            <ProtectedRoute>
              <Routes>
                <Route path="/" element={
                  <MainLayout>
                    <HomePage />
                  </MainLayout>
                } />
                <Route path="/chat" element={
                  <MainLayout>
                    <ChatPage />
                  </MainLayout>
                } />
                <Route path="/chat/:chatId" element={
                  <MainLayout>
                    <ChatPage />
                  </MainLayout>
                } />
                <Route path="/workspace/:workspaceId/chat" element={
                  <MainLayout>
                    <ChatPage />
                  </MainLayout>
                } />
                <Route path="/workspace/:workspaceId/chat/:chatId" element={
                  <MainLayout>
                    <ChatPage />
                  </MainLayout>
                } />
                <Route path="/upload" element={
                  <MainLayout>
                    <UploadPage />
                  </MainLayout>
                } />
                <Route path="/reports" element={
                  <MainLayout>
                    <ReportsPage />
                  </MainLayout>
                } />
                <Route path="/workspace" element={
                  <MainLayout>
                    <WorkspacePage />
                  </MainLayout>
                } />
                <Route path="/workspace/create" element={
                  <MainLayout>
                    <CreateWorkspacePage />
                  </MainLayout>
                } />
                <Route path="/workspace/:workspaceId" element={
                  <MainLayout>
                    <WorkspacePage />
                  </MainLayout>
                } />
              </Routes>
            </ProtectedRoute>
          } />
        </Routes>
      </BrowserRouter>
    </ToastProvider>
  );
}

export default App;
