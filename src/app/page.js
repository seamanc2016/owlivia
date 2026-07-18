"use client"
import { Hero } from "@/components/ui/hero";


export default function Home() {
  return (
    <>
    <section className="hero h-full">
      <Hero
        title={"MEET\nOWLIVIA"}
        description="The Advising Assistant That Never Clocks Out. Get quick answers about FAU advising, deadlines, forms, and academic resources."
        buttonText="Start Chatting"
        mobileImage="/owlivia_small_bg.png"
        desktopBackgroundImage="/owlivia_large_bg_1.png"
        onButtonClick={() => {
          console.log("Start chatting")
        }}
      />
    </section>

    <section className="features">
    </section>

    <section className="how-it-works">
    </section>

    <section className="demo">
    </section>

    <section className="about">
    </section>

    <footer>
    </footer>
    </>
  );
}
