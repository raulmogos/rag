import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { MantineProvider, createTheme } from "@mantine/core";
import "@mantine/core/styles.css";
import App from "./App";
import "./index.css";

const theme = createTheme({
  primaryColor: "indigo",
  defaultRadius: "lg",
  fontFamily:
    "Inter, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif",
});

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <MantineProvider theme={theme} defaultColorScheme="light">
      <App />
    </MantineProvider>
  </StrictMode>,
);
