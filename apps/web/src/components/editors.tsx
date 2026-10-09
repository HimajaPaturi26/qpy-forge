"use client";

import CodeMirror from "@uiw/react-codemirror";
import { python } from "@codemirror/lang-python";
import { oneDark } from "@codemirror/theme-one-dark";
import { qLanguage } from "@/lib/q-language";

const editorHeight = "min(26rem, 54vh)";

const shared = {
  theme: oneDark,
  height: editorHeight,
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
    <div className="overflow-hidden rounded-md border border-line focus-within:border-amber">
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

export function EditorPlaceholder({ children }: { children: string }) {
  return (
    <div
      className="flex items-center justify-center rounded-md border border-dashed border-line px-6 text-center text-sm text-muted"
      style={{ height: editorHeight }}
    >
      {children}
    </div>
  );
}
