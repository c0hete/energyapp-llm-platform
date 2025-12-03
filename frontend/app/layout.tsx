import type { Metadata } from "next";
import { Montserrat, JetBrains_Mono } from "next/font/google";
import QueryProvider from "@/providers/QueryProvider";
import { SessionErrorProvider } from "@/providers/SessionErrorProvider";
import { ErrorBoundaryProvider } from "@/providers/ErrorBoundaryProvider";
import "./globals.css";

const montserrat = Montserrat({
  variable: "--font-sans",
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "EnergyApp LLM",
  description: "Chat LLM con Qwen 2.5:3B",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es">
      <body
        className={`${montserrat.variable} ${jetbrainsMono.variable} antialiased`}
      >
        <ErrorBoundaryProvider>
          <QueryProvider>
            <SessionErrorProvider>{children}</SessionErrorProvider>
          </QueryProvider>
        </ErrorBoundaryProvider>
      </body>
    </html>
  );
}
