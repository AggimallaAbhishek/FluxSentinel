export default function BlockedIPTable({ blockedIps }) {
  return (
    <div className="rounded-xl bg-white/80 p-4 shadow-sm">
      <h3 className="mb-3 text-lg font-semibold">Blocked IPs</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-slate-200 text-slate-600">
              <th className="py-2">IP</th>
              <th className="py-2">Blocked At</th>
              <th className="py-2">Reason</th>
            </tr>
          </thead>
          <tbody>
            {blockedIps.length === 0 && (
              <tr>
                <td className="py-3 text-slate-500" colSpan={3}>
                  No blocked IPs yet.
                </td>
              </tr>
            )}
            {blockedIps.map((entry) => (
              <tr key={`${entry.ip}-${entry.blocked_at}`} className="border-b border-slate-100">
                <td className="py-2 font-mono">{entry.ip}</td>
                <td className="py-2">{new Date(entry.blocked_at).toLocaleString()}</td>
                <td className="py-2">{entry.reason}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
