import type { Metadata } from "next";
import type { ReactNode } from "react";
import { Geist_Mono, Montserrat } from "next/font/google";
import { Shell } from "@/components/shell";
import "./globals.css";

const montserrat = Montserrat({
  variable: "--font-montserrat",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Q2Py Forge",
  description: "Translate supported Q/kdb+ expressions into Python and validate results against authored expectations.",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en">
      <body className={`${montserrat.variable} ${geistMono.variable} antialiased`}>
        <Shell>{children}</Shell>
      </body>
    </html>
  );
}
