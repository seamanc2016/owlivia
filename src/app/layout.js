import { ThemeProvider } from "@/components/theme-provider"
import { Inter, Cormorant_Garamond } from "next/font/google";
import { Navbar } from "@/components/ui/navbar";
import "./globals.css";

const fontSans = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
});

const fontSerif = Cormorant_Garamond({
  subsets: ["latin"],
  variable: "--font-serif",
});


export const metadata = {
  title: "Owlivia",
  description: "STEM Graduate AI Assistant",
};

export default function RootLayout({ children }) {
  return (
    <html
      lang="en"
      className={`${fontSans.variable} ${fontSerif.variable}  h-full antialiased`}
      suppressHydrationWarning
    >
      <body className="min-h-full flex flex-col">
          <ThemeProvider
            attribute="class"
            defaultTheme="system"
            enableSystem
            disableTransitionOnChange
          >
            <Navbar/>
            {children}
          </ThemeProvider>
      </body>
    </html>
  );
}
