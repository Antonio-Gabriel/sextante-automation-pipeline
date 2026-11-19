// The simulated API of the frontend tests: no test reaches a real server.
import { setupServer } from "msw/node";

export const server = setupServer();
