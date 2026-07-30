import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { ThemeProvider } from "./app/providers/ThemeProvider";
import { LanguageProvider } from "./app/providers/LanguageProvider";
import { MockAuthProvider } from "./app/providers/AuthProvider";
import { AppRoutes } from "./app/router/Routes";
import { ErrorBoundary } from "./components/feedback/ErrorBoundary";
import "./styles.css";
ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <ThemeProvider>
        <LanguageProvider>
          <BrowserRouter>
            <MockAuthProvider>
              <AppRoutes />
            </MockAuthProvider>
          </BrowserRouter>
        </LanguageProvider>
      </ThemeProvider>
    </ErrorBoundary>
  </React.StrictMode>,
);
