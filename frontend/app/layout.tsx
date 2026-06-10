import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "RecordChat — IATA ONE Record assistant",
  description:
    "A domain-specific AI assistant for IATA ONE Record: data model, JSON-LD, API, and relationships.",
  icons: {
    icon: "/recordchat-mark.svg",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
