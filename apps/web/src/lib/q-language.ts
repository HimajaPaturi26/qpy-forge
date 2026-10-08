import { StreamLanguage } from "@codemirror/language";

const KEYWORDS = /^(select|exec|update|delete|from|where|by|do|while|if)\b/;

export const qLanguage = StreamLanguage.define({
  name: "q",
  token(stream) {
    if (stream.eatSpace()) {
      if (stream.peek() === "/") {
        stream.skipToEnd();
        return "comment";
      }
      return null;
    }
    if (stream.match(KEYWORDS)) {
      return "keyword";
    }
    if (stream.match(/^0[NnWw][hijef]?/)) {
      return "number";
    }
    if (stream.match(/^[0-9]{4}\.[0-9]{2}\.[0-9]{2}(D[0-9:.]+)?/)) {
      return "number";
    }
    if (stream.match(/^-?\d+(\.\d+)?([eE][+-]?\d+)?[hijef]?/)) {
      return "number";
    }
    if (stream.match(/^`[A-Za-z0-9_.]*/)) {
      return "string";
    }
    if (stream.match(/^"([^"\\]|\\.)*"/)) {
      return "string";
    }
    if (stream.match(/^'[^']'/)) {
      return "string";
    }
    if (stream.match(/^[A-Za-z_][A-Za-z0-9_.]*/)) {
      return "variableName";
    }
    if (stream.match(/^[{}()[\];]/)) {
      return "bracket";
    }
    if (stream.match(/^[+\-*%=<>~,#_!$?@.|&^:\\/']+/)) {
      return "operator";
    }
    stream.next();
    return null;
  },
});
