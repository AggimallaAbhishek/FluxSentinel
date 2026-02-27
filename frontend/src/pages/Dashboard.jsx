import { useEffect, useMemo, useState } from "react";

import BlockedIPTable from "../components/BlockedIPTable";
import Heatmap from "../components/Heatmap";
import SeverityGauge from "../components/SeverityGauge";
import TrafficChart from "../components/TrafficChart";
import api from "../services/api";
import { createAlertsSocket } from "../services/websocket";

const POLL_INTERVAL_MS = 10000;
const MAX_EVENTS = 50;
const DEFAULT_TRAFFIC = [
  { time: "00:00", requestRate: 12 },
  { time: "00:10", requestRate: 15 },
  { time: "00:20", requestRate: 11 },
  { time: "00:30", requestRate: 21 }
];

function sortByTimestampDesc(a, b) {
  const aTime = Date.parse(a.timestamp || a.blocked_at || "") || 0;
  const bTime = Date.parse(b.timestamp || b.blocked_at || "") || 0;
  return bTime - aTime;
}

function normalizeEvent(event) {
  return {
    ip: event.ip,
    action: event.action || "temporary_block",
    severity: Number(event.severity) || 0,
    probability:
      event.probability !== undefined && event.probability !== null
        ? Number(event.probability)
        : undefined,
    timestamp: event.timestamp || new Date().toISOString()
  };
}

function mergeEvents(existing, incoming) {
  const map = new Map();

  [...existing, ...incoming]
    .map(normalizeEvent)
    .forEach((event) => {
      const key = `${event.ip}|${event.action}|${event.timestamp}`;
      map.set(key, event);
    });

  return Array.from(map.values()).sort(sortByTimestampDesc).slice(0, MAX_EVENTS);
}

function mergeBlockedIps(existing, incoming) {
  const map = new Map();

  [...existing, ...incoming].forEach((item) => {
    const normalized = {
      ip: item.ip,
      blocked_at: item.blocked_at || new Date().toISOString(),
      reason: item.reason || "ml_detected_attack"
    };

    const key = `${normalized.ip}|${normalized.blocked_at}|${normalized.reason}`;
    map.set(key, normalized);
  });

  return Array.from(map.values()).sort(sortByTimestampDesc).slice(0, MAX_EVENTS);
}

function buildTrafficData(events) {
  if (!events.length) {
    return DEFAULT_TRAFFIC;
  }

  const points = [...events]
    .sort((a, b) => (Date.parse(a.timestamp) || 0) - (Date.parse(b.timestamp) || 0))
    .slice(-20)
    .map((event) => {
      const requestRate =
        event.probability !== undefined
          ? Math.round(event.probability * 250)
          : Math.round((Number(event.severity) || 0) * 2.5);

      return {
        time: new Date(event.timestamp).toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit"
        }),
        requestRate
      };
    });

  return points.length ? points : DEFAULT_TRAFFIC;
}

export default function Dashboard() {
  const [blockedIps, setBlockedIps] = useState([]);
  const [events, setEvents] = useState([]);

  useEffect(() => {
    let isMounted = true;

    async function syncFromApi() {
      try {
        const [blockedIpsResponse, eventsResponse] = await Promise.all([
          api.get("/blocked-ips"),
          api.get("/mitigation-events")
        ]);

        if (!isMounted) {
          return;
        }

        setBlockedIps((prev) => mergeBlockedIps(prev, blockedIpsResponse.data));
        setEvents((prev) => mergeEvents(prev, eventsResponse.data));
      } catch (error) {
        console.error("Failed to sync dashboard data", error);
      }
    }

    syncFromApi();
    const intervalId = window.setInterval(syncFromApi, POLL_INTERVAL_MS);

    return () => {
      isMounted = false;
      window.clearInterval(intervalId);
    };
  }, []);

  useEffect(() => {
    const socket = createAlertsSocket();

    socket.on("connect_error", (error) => {
      console.error("Socket connection error", error);
    });

    socket.on("threat_alert", (payload) => {
      setEvents((prev) => mergeEvents(prev, [payload]));
      setBlockedIps((prev) =>
        mergeBlockedIps(prev, [
          {
            ip: payload.ip,
            blocked_at: payload.timestamp,
            reason: payload.action
          }
        ])
      );
    });

    return () => {
      socket.disconnect();
    };
  }, []);

  const traffic = useMemo(() => buildTrafficData(events), [events]);
  const latestSeverity = events[0]?.severity || 0;

  const heatmapIntensity = useMemo(() => {
    const base = new Array(24).fill(0);
    events.forEach((event, index) => {
      base[index % 24] = Math.max(base[index % 24], event.severity || 0);
    });
    return base;
  }, [events]);

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
