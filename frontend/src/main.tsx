import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { App } from "./app";
import { createQueryClient } from "./query-client";
import { createAppRouter } from "./router";
import "./styles.css";

const queryClient = createQueryClient();
const router = createAppRouter(queryClient);
const root = document.getElementById("root");

if (root !== null) {
  createRoot(root).render(
    <StrictMode>
      <App queryClient={queryClient} router={router} />
    </StrictMode>,
  );
}
