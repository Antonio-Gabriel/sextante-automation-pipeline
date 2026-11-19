// Minimal Chrome DevTools Protocol driver for the documentation build: one headless
// Chrome, one page, no network beyond file:// (the pages load only local files).
import { spawn } from "node:child_process";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const PORT = 9334;
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

/**
 * Start headless Chrome and return helpers bound to its only page.
 *
 * Example:
 *   const page = await openPage(); await page.goto("file:///tmp/x.html"); await page.close();
 */
export async function openPage() {
  const profile = mkdtempSync(join(tmpdir(), "sextante-docs-"));
  const chrome = spawn(
    process.env.CHROME ?? "google-chrome",
    ["--headless=new", `--remote-debugging-port=${PORT}`, `--user-data-dir=${profile}`,
      "--no-first-run", "--no-default-browser-check", "--allow-file-access-from-files", "about:blank"],
    { stdio: "ignore" },
  );
  const target = await findPage();
  const ws = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((resolve) => ws.addEventListener("open", resolve));
  const pending = new Map();
  let nextId = 0;
  ws.addEventListener("message", (event) => {
    const message = JSON.parse(event.data);
    if (message.id && pending.has(message.id)) {
      pending.get(message.id)(message);
      pending.delete(message.id);
    }
  });
  const send = (method, params = {}) =>
    new Promise((resolve) => {
      const id = ++nextId;
      pending.set(id, resolve);
      ws.send(JSON.stringify({ id, method, params }));
    }).then((message) => {
      if (message.error) throw new Error(`${method}: ${message.error.message}`);
      return message.result;
    });
  const evaluate = async (expression) => {
    const { result, exceptionDetails } = await send("Runtime.evaluate", {
      expression, awaitPromise: true, returnByValue: true,
    });
    if (exceptionDetails) throw new Error(exceptionDetails.exception?.description ?? exceptionDetails.text);
    return result.value;
  };
  await send("Page.enable");
  await send("Runtime.enable");
  return {
    send,
    evaluate,
    async goto(url) {
      await send("Page.navigate", { url });
      for (let i = 0; i < 100; i++) {
        if (await evaluate("document.readyState === 'complete'")) return;
        await sleep(100);
      }
      throw new Error(`page did not load: ${url}`);
    },
    async close() {
      ws.close();
      chrome.kill();
      await sleep(300);
      rmSync(profile, { recursive: true, force: true });
    },
  };
}

async function findPage() {
  for (let i = 0; i < 100; i++) {
    try {
      const targets = await (await fetch(`http://127.0.0.1:${PORT}/json`)).json();
      const page = targets.find((target) => target.type === "page");
      if (page) return page;
    } catch {
      // Chrome is still starting.
    }
    await sleep(100);
  }
  throw new Error("headless Chrome did not start");
}
