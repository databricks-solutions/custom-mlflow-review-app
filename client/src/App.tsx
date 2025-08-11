import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { WelcomePage } from "./pages/WelcomePage";
import { ReviewAppPage } from "./pages/ReviewAppPage";
import { LabelingPage } from "./pages/LabelingPage";
import { DeveloperDashboard } from "./pages/DeveloperDashboard";
import { LabelingSchemasPage } from "./pages/LabelingSchemasPage";
import { PreviewPage } from "./pages/PreviewPage";
import { ProtectedRoute } from "./components/ProtectedRoute";

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-background">
        <Routes>
          <Route path="/" element={<LabelingPage />} />
          <Route
            path="/dev"
            element={
              <ProtectedRoute requireDeveloper={true}>
                <DeveloperDashboard />
              </ProtectedRoute>
            }
          />
          <Route path="/welcome" element={<WelcomePage />} />
          <Route
            path="/labeling-schemas"
            element={
              <ProtectedRoute requireDeveloper={true}>
                <LabelingSchemasPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/preview/:sessionId"
            element={
              <ProtectedRoute requireDeveloper={true}>
                <PreviewPage />
              </ProtectedRoute>
            }
          />
          <Route path="/review-app/:reviewAppId" element={<ReviewAppPage />} />
          <Route path="/review/:sessionId" element={<ReviewAppPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
