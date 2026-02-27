import { io } from "socket.io-client";

export function createAlertsSocket() {
  const baseUrl = import.meta.env.VITE_SOCKET_URL || "http://localhost:5000";
  return io(`${baseUrl}/alerts`, {
    transports: ["websocket"],
    withCredentials: false
  });
}
