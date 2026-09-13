import type { Metadata, Viewport } from "next";
import { ClerkProvider } from "@clerk/nextjs";
import { clerkPublishableKey } from "@/lib/authMode";
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
  const publishableKey = clerkPublishableKey();
  const tree = (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
  if (!publishableKey) {
    return tree;
  }
  return <ClerkProvider publishableKey={publishableKey}>{tree}</ClerkProvider>;
}
