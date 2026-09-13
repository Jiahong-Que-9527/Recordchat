import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "RecordChat — IATA ONE Record assistant",
  description:
    "A domain-specific AI assistant for IATA ONE Record: data model, JSON-LD, API, and relationships.",
  icons: {
    icon: [
      { url: "/recordchat-icon.png", sizes: "any", type: "image/png" },
      { url: "/recordchat-icon.png", sizes: "1254x1254", type: "image/png" },
    ],
    apple: "/recordchat-icon.png",
  },
};

export const viewport: Viewport = {
  themeColor: "#f4f8fe",
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
