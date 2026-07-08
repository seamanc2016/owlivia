import { Inter, Cormorant } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-sans",
  subsets: ["latin"],
});

const cormorant = Cormorant({
    subsets: ["latin"],
})



export const metadata = {
  title: "Owlivia",
  description: "STEM Graduate AI Assistant",
};

export default function RootLayout({ children }) {
  return (
    <html
      lang="en"
      className={`${inter.variable}  h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
