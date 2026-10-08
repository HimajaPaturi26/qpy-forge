"use client";

import CodeMirror from "@uiw/react-codemirror";
import { python } from "@codemirror/lang-python";
import { oneDark } from "@codemirror/theme-one-dark";
import { qLanguage } from "@/lib/q-language";

const shared = {
  theme: oneDark,
  height: "320px",
  basicSetup: {
    lineNumbers: true,
    foldGutter: false,
    highlightActiveLine: true,
  },
};

export function QEditor({
  value,
  onChange,
}: {
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <div className="overflow-hidden rounded-md border border-line">
      <CodeMirror
        value={value}
        height={shared.height}
        theme={shared.theme}
        basicSetup={shared.basicSetup}
        extensions={[qLanguage]}
        onChange={onChange}
        aria-label="Q source"
      />
    </div>
  );
}

export function PythonEditor({ value }: { value: string }) {
  return (
    <div className="overflow-hidden rounded-md border border-line">
      <CodeMirror
        value={value}
        height={shared.height}
        theme={shared.theme}
        basicSetup={shared.basicSetup}
        extensions={[python()]}
        editable={false}
        readOnly
        aria-label="Generated Python"
      />
    </div>
  );
}
