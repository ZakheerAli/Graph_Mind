import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "GraphMind",
  description: "Ask questions about your documents and get cited answers.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
