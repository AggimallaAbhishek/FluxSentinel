import { useEffect, useMemo, useState } from "react";

import BlockedIPTable from "../components/BlockedIPTable";
import Heatmap from "../components/Heatmap";
import SeverityGauge from "../components/SeverityGauge";
import TrafficChart from "../components/TrafficChart";
import api from "../services/api";
import { createAlertsSocket } from "../services/websocket";

export default function Dashboard() {
  const [blockedIps, setBlockedIps] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [traffic, setTraffic] = useState([
    { time: "00:00", requestRate: 12 },
    { time: "00:10", requestRate: 15 },
    { time: "00:20", requestRate: 11 },
    { time: "00:30", requestRate: 21 }
  ]);

  useEffect(() => {
    async function fetchBlockedIps() {
      try {
        const response = await api.get("/blocked-ips");
        setBlockedIps(response.data);
      } catch (error) {
        console.error("Failed to load blocked IPs", error);
      }
    }

    fetchBlockedIps();
  }, []);

  useEffect(() => {
    const socket = createAlertsSocket();

    socket.on("threat_alert", (payload) => {
      setAlerts((prev) => [payload, ...prev].slice(0, 20));

      setTraffic((prev) => {
        const next = [...prev, {
          time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          requestRate: Math.round(payload.probability * 250)
        }];
        return next.slice(-20);
      });

      setBlockedIps((prev) => {
        const next = [{ ip: payload.ip, blocked_at: payload.timestamp, reason: payload.action }, ...prev];
        return next.slice(0, 50);
      });
    });

    return () => {
      socket.disconnect();
    };
  }, []);

  const latestSeverity = alerts[0]?.severity || 0;

  const heatmapIntensity = useMemo(() => {
    const base = new Array(24).fill(0);
    alerts.forEach((alert, index) => {
      base[index % 24] = Math.max(base[index % 24], alert.severity || 0);
    });
    return base;
  }, [alerts]);

  return (
    <main className="mx-auto max-w-7xl space-y-6 px-4 py-8">
      <header className="rounded-2xl bg-ink p-6 text-white">
        <p className="text-sm uppercase tracking-[0.2em] text-cyan-300">FluxSentinel</p>
        <h1 className="mt-2 text-3xl font-bold">Distributed Threat Detection Dashboard</h1>
      </header>

      <section className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <TrafficChart data={traffic} />
        </div>
        <SeverityGauge severity={latestSeverity} />
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <Heatmap intensity={heatmapIntensity} />
        <BlockedIPTable blockedIps={blockedIps} />
      </section>
    </main>
  );
}
