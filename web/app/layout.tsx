import type { Metadata } from "next";
import "./globals.css";

const url = "https://claim-chart.kareemghazal.com";
const title = "claim-chart — map a patent claim against prior art";
const description =
  "Paste an independent patent claim and a prior-art reference; it splits the claim into limitations and maps each to a verbatim quote in the reference (or marks it not disclosed), then gives a novelty verdict — grounded so it can't invent a disclosure. Educational — not legal advice.";

export const metadata: Metadata = {
  metadataBase: new URL(url),
  title,
  description,
  alternates: { canonical: "/" },
  openGraph: {
    type: "website",
    url,
    siteName: "claim-chart",
    title,
    description,
    locale: "en_GB",
    images: [{ url: "/og.jpg", width: 1200, height: 630, alt: "claim-chart — AI patent claim-chart / prior-art anticipation tool" }],
  },
  twitter: { card: "summary_large_image", title, description, images: ["/og.jpg"] },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
