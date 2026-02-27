const CELL_COUNT = 24;

export default function Heatmap({ intensity = [] }) {
  const values = [...intensity];
  while (values.length < CELL_COUNT) {
    values.push(0);
  }

  return (
    <div className="rounded-xl bg-white/80 p-4 shadow-sm">
      <h3 className="mb-3 text-lg font-semibold">Attack Heatmap</h3>
      <div className="grid grid-cols-6 gap-2 sm:grid-cols-8 lg:grid-cols-12">
        {values.slice(0, CELL_COUNT).map((value, index) => {
          const opacity = Math.max(0.12, Math.min(1, value / 100));
          return (
            <div
              key={index}
              className="h-8 rounded"
              style={{ backgroundColor: `rgba(185, 28, 28, ${opacity})` }}
              title={`Slot ${index + 1}: ${value}`}
            />
          );
        })}
      </div>
    </div>
  );
}
