export default function SeverityGauge({ severity }) {
  const boundedSeverity = Math.max(0, Math.min(100, severity));

  return (
    <div className="rounded-xl bg-white/80 p-4 shadow-sm">
      <h3 className="mb-3 text-lg font-semibold">Severity Score</h3>
      <div className="h-3 w-full overflow-hidden rounded-full bg-slate-200">
        <div
          className="h-full rounded-full bg-gradient-to-r from-amber-400 to-red-600 transition-all"
          style={{ width: `${boundedSeverity}%` }}
        />
      </div>
      <p className="mt-3 text-2xl font-bold text-threat">{boundedSeverity}/100</p>
    </div>
  );
}
