import type { Metadata } from "next";
import type { ReactNode } from "react";
import { Barlow, Barlow_Semi_Condensed, Red_Hat_Mono } from "next/font/google";

import { Providers } from "@/app/providers";

import "./globals.css";

const barlow = Barlow({
  subsets: ["latin"],
  variable: "--font-barlow",
  weight: ["400", "500", "600", "700"],
});

const barlowSemiCondensed = Barlow_Semi_Condensed({
  subsets: ["latin"],
  variable: "--font-barlow-semi-condensed",
  weight: ["500", "600"],
});

const redHatMono = Red_Hat_Mono({
  subsets: ["latin"],
  variable: "--font-red-hat-mono",
  weight: ["400", "500"],
});

export const metadata: Metadata = {
  title: "Nebula · consola",
  description: "Consola del gateway Nebula: ruteo por niveles, ledger de costos y evaluación del router.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: ReactNode;
}>) {
  return (
    <html lang="es" className={`${barlow.variable} ${barlowSemiCondensed.variable} ${redHatMono.variable}`}>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
