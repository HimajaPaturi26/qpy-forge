export function JsonBlock({ value }: { value: unknown }) {
  return (
    <pre className="max-h-80 overflow-auto rounded-md border border-line bg-black/30 p-3 font-mono text-xs leading-5 text-paper">
      {JSON.stringify(value, null, 2)}
    </pre>
  );
}
