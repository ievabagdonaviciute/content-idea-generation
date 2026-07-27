import type { Metadata } from "next";
import { APP_NAME } from "@/lib/config";
import { QueryProvider } from "@/lib/query-provider";
import { Nav } from "@/components/Nav";
import "./globals.css";

export const metadata: Metadata = {
  title: APP_NAME,
  description: "Personal AI-assisted TikTok content planning platform.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <QueryProvider>
          <Nav />
          <main className="mx-auto max-w-3xl px-4 py-8">{children}</main>
        </QueryProvider>
      </body>
    </html>
  );
}
