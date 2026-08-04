"use client"
import { Hero } from "@/components/ui/hero";
import { Navbar } from "@/components/ui/landing-navbar";
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import {
  Alert,
  AlertDescription,
  AlertTitle,
} from "@/components/ui/alert";
import {
  ArrowRight,
  BookOpen,
  CheckCircle2,
  Clock3,
  MessageCircle,
  Search,
  ShieldCheck,
  UserRoundCheck,
} from "lucide-react";
import Link from "next/link";



export default function Home() {
  return (
    <>
      <Navbar />
      <div className="h-screen">
        
        <section id="home" className="hero h-full scroll-mt-16">
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

        <section id="features" className="features scroll-mt-16">
          <div className="bg-muted/40 px-5 py-20 md:px-8 lg:py-28">
            <div className="mx-auto max-w-6xl">
              <div className="mx-auto mb-12 max-w-2xl text-center">
                <Badge variant="secondary" className="mb-4">
                  Built for FAU students
                </Badge>

                <h2 className="text-3xl font-bold tracking-tight md:text-4xl">
                  Advising information without the wait
                </h2>

                <p className="mt-4 text-base leading-7 text-muted-foreground md:text-lg">
                  Owlivia helps students find common advising information while
                  allowing human advisors to focus on concerns that require
                  personal attention.
                </p>
              </div>

              <div className="grid gap-6 md:grid-cols-2">
                <Card className="transition-transform duration-200 hover:-translate-y-1">
                  <CardHeader>
                    <div className="mb-3 flex items-start justify-between gap-4">
                      <div className="flex size-11 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                        <Clock3 className="size-5" />
                      </div>

                      <Badge variant="outline">Available anytime</Badge>
                    </div>

                    <CardTitle className="text-xl">
                      Help Outside Office Hours
                    </CardTitle>

                    <CardDescription className="leading-6">
                      Students can ask common advising questions without waiting
                      for an appointment or standing in a long advising line.
                    </CardDescription>
                  </CardHeader>
                </Card>

                <Card className="transition-transform duration-200 hover:-translate-y-1">
                  <CardHeader>
                    <div className="mb-3 flex items-start justify-between gap-4">
                      <div className="flex size-11 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                        <Search className="size-5" />
                      </div>

                      <Badge variant="outline">FAU sources</Badge>
                    </div>

                    <CardTitle className="text-xl">
                      Grounded Responses
                    </CardTitle>

                    <CardDescription className="leading-6">
                      Owlivia searches public FAU resources before generating
                      an answer and provides the supporting source links.
                    </CardDescription>
                  </CardHeader>
                </Card>

                <Card className="transition-transform duration-200 hover:-translate-y-1">
                  <CardHeader>
                    <div className="mb-3 flex items-start justify-between gap-4">
                      <div className="flex size-11 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                        <BookOpen className="size-5" />
                      </div>

                      <Badge variant="outline">Graduate advising</Badge>
                    </div>

                    <CardTitle className="text-xl">
                      Common Academic Questions
                    </CardTitle>

                    <CardDescription className="leading-6">
                      Find information about course requirements, forms,
                      deadlines, graduation, and department procedures.
                    </CardDescription>
                  </CardHeader>
                </Card>

                <Card className="transition-transform duration-200 hover:-translate-y-1">
                  <CardHeader>
                    <div className="mb-3 flex items-start justify-between gap-4">
                      <div className="flex size-11 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                        <UserRoundCheck className="size-5" />
                      </div>

                      <Badge variant="outline">Human support</Badge>
                    </div>

                    <CardTitle className="text-xl">
                      Advisor Escalation
                    </CardTitle>

                    <CardDescription className="leading-6">
                      Questions involving private records, official approval, or
                      student-specific decisions are directed to a human advisor.
                    </CardDescription>
                  </CardHeader>
                </Card>
              </div>
            </div>
          </div>
        </section>

        <section
          id="how-it-works"
          className="how-it-works scroll-mt-16"
        >
          <div className="bg-primary px-5 py-20 text-primary-foreground md:px-8 lg:py-28">
            <div className="mx-auto max-w-6xl">
              <div className="mx-auto mb-12 max-w-2xl text-center">
                <Badge variant="secondary" className="mb-4">
                  How it works
                </Badge>

                <h2 className="text-3xl font-bold tracking-tight md:text-4xl">
                  From question to trusted information
                </h2>

                <p className="mt-4 text-base leading-7 text-primary-foreground/75 md:text-lg">
                  Owlivia combines a conversational interface with information
                  retrieved from public FAU resources.
                </p>
              </div>

              <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
                <Card className="border-primary-foreground/15 bg-primary-foreground/10 text-primary-foreground ring-primary-foreground/15">
                  <CardHeader>
                    <div className="mb-5 flex items-center justify-between">
                      <span className="text-3xl font-bold text-primary-foreground/30">
                        01
                      </span>

                      <div className="flex size-10 items-center justify-center rounded-full bg-primary-foreground text-primary">
                        <MessageCircle className="size-5" />
                      </div>
                    </div>

                    <CardTitle>
                      Ask a Question
                    </CardTitle>

                    <CardDescription className="leading-6 text-primary-foreground/70">
                      Enter an advising question in your own words or select one
                      of Owlivia&apos;s suggested conversation topics.
                    </CardDescription>
                  </CardHeader>
                </Card>

                <Card className="border-primary-foreground/15 bg-primary-foreground/10 text-primary-foreground ring-primary-foreground/15">
                  <CardHeader>
                    <div className="mb-5 flex items-center justify-between">
                      <span className="text-3xl font-bold text-primary-foreground/30">
                        02
                      </span>

                      <div className="flex size-10 items-center justify-center rounded-full bg-primary-foreground text-primary">
                        <Search className="size-5" />
                      </div>
                    </div>

                    <CardTitle>
                      Search FAU Resources
                    </CardTitle>

                    <CardDescription className="leading-6 text-primary-foreground/70">
                      Owlivia retrieves relevant information from publicly
                      available pages on the FAU website.
                    </CardDescription>
                  </CardHeader>
                </Card>

                <Card className="border-primary-foreground/15 bg-primary-foreground/10 text-primary-foreground ring-primary-foreground/15">
                  <CardHeader>
                    <div className="mb-5 flex items-center justify-between">
                      <span className="text-3xl font-bold text-primary-foreground/30">
                        03
                      </span>

                      <div className="flex size-10 items-center justify-center rounded-full bg-primary-foreground text-primary">
                        <BookOpen className="size-5" />
                      </div>
                    </div>

                    <CardTitle>
                      Receive an Answer
                    </CardTitle>

                    <CardDescription className="leading-6 text-primary-foreground/70">
                      Gemini uses the retrieved information to generate a clear
                      response supported by visible source links.
                    </CardDescription>
                  </CardHeader>
                </Card>

                <Card className="border-primary-foreground/15 bg-primary-foreground/10 text-primary-foreground ring-primary-foreground/15">
                  <CardHeader>
                    <div className="mb-5 flex items-center justify-between">
                      <span className="text-3xl font-bold text-primary-foreground/30">
                        04
                      </span>

                      <div className="flex size-10 items-center justify-center rounded-full bg-primary-foreground text-primary">
                        <UserRoundCheck className="size-5" />
                      </div>
                    </div>

                    <CardTitle>
                      Contact an Advisor
                    </CardTitle>

                    <CardDescription className="leading-6 text-primary-foreground/70">
                      Owlivia recommends human assistance when a question
                      requires official judgment or access to student records.
                    </CardDescription>
                  </CardHeader>
                </Card>
              </div>

              <Alert className="mt-10 border-primary-foreground/20 bg-primary-foreground/10 text-primary-foreground">
                <ShieldCheck className="size-4" />

                <AlertTitle>
                  Owlivia supports human advisors
                </AlertTitle>

                <AlertDescription className="text-primary-foreground/70">
                  Owlivia provides general advising information. It does not
                  make official academic decisions or replace the responsibility
                  of an FAU advisor.
                </AlertDescription>
              </Alert>
            </div>
          </div>
        </section>

        <section id="demo" className="demo scroll-mt-16">
          <div className="bg-muted/40 px-5 py-20 md:px-8 lg:py-28">
            <div className="mx-auto max-w-6xl">
              <div className="mx-auto mb-12 max-w-2xl text-center">
                <Badge variant="secondary" className="mb-4">
                  Project Demonstration
                </Badge>

                <h2 className="text-3xl font-bold tracking-tight md:text-4xl">
                  Owlivia Explained By The Developers
                </h2>

                <p className="mt-4 leading-7 text-muted-foreground md:text-lg">
                  Watch the demonstration to get a better understanding of how
                  the application can revolutionize academic advising.
                </p>
              </div>

              <div className="mx-auto max-w-5xl overflow-hidden rounded-2xl bg-black shadow-xl ring-1 ring-foreground/10">
                <div className="relative aspect-video w-full">
                  <iframe
                    src="https://www.youtube.com/embed/lnAYj85t7UQ"
                    title="Owlivia Project Demonstration"
                    className="absolute inset-0 h-full w-full"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                    referrerPolicy="strict-origin-when-cross-origin"
                    allowFullScreen
                  />
                </div>
              </div>
            </div>
          </div>
        </section>

        <section id="about" className="about scroll-mt-16">
          <div className="bg-primary px-5 py-20 text-primary-foreground md:px-8 lg:py-28">
            <div className="mx-auto max-w-6xl">
              <div className="mx-auto max-w-3xl text-center">
                <Badge variant="secondary" className="mb-4">
                  About the project
                </Badge>

                <h2 className="text-3xl font-bold tracking-tight md:text-4xl">
                  Built to make advising information easier to reach
                </h2>

                <p className="mt-5 leading-7 text-primary-foreground/75 md:text-lg">
                  Owlivia is a prototype graduate advising assistant developed
                  for students in Florida Atlantic University&apos;s College of
                  Engineering and Computer Science. It was designed to answer
                  common questions while reducing the repetitive workload
                  placed on academic advisors.
                </p>

                <p className="mt-4 leading-7 text-primary-foreground/75 md:text-lg">
                  The application uses Gemini to generate responses and Tavily
                  to retrieve information from public FAU resources. Retrieved
                  sources are displayed with the answer so students can review
                  the original university webpages.
                </p>
              </div>

              <div className="mt-12 grid gap-6 md:grid-cols-2">
                <Card className="border-primary-foreground/15 bg-primary-foreground/10 text-primary-foreground ring-primary-foreground/15">
                  <CardHeader>
                    <CheckCircle2 className="mb-3 size-6 text-primary-foreground" />

                    <CardTitle>
                      Focused on FAU Information
                    </CardTitle>

                    <CardDescription className="leading-6 text-primary-foreground/70">
                      Owlivia searches publicly available FAU webpages for
                      relevant advising information instead of relying only on
                      the model&apos;s existing knowledge.
                    </CardDescription>
                  </CardHeader>
                </Card>

                <Card className="border-primary-foreground/15 bg-primary-foreground/10 text-primary-foreground ring-primary-foreground/15">
                  <CardHeader>
                    <CheckCircle2 className="mb-3 size-6 text-primary-foreground" />

                    <CardTitle>
                      Sources Students Can Review
                    </CardTitle>

                    <CardDescription className="leading-6 text-primary-foreground/70">
                      The interface displays links returned by the retrieval
                      system, allowing students to verify important information
                      directly.
                    </CardDescription>
                  </CardHeader>
                </Card>

                <Card className="border-primary-foreground/15 bg-primary-foreground/10 text-primary-foreground ring-primary-foreground/15">
                  <CardHeader>
                    <CheckCircle2 className="mb-3 size-6 text-primary-foreground" />

                    <CardTitle>
                      Designed for Common Questions
                    </CardTitle>

                    <CardDescription className="leading-6 text-primary-foreground/70">
                      The assistant can help with general questions involving
                      forms, deadlines, degree requirements, courses, and
                      department procedures.
                    </CardDescription>
                  </CardHeader>
                </Card>

                <Card className="border-primary-foreground/15 bg-primary-foreground/10 text-primary-foreground ring-primary-foreground/15">
                  <CardHeader>
                    <CheckCircle2 className="mb-3 size-6 text-primary-foreground" />

                    <CardTitle>
                      Human Advisors Remain Essential
                    </CardTitle>

                    <CardDescription className="leading-6 text-primary-foreground/70">
                      Requests involving private records, individual degree
                      decisions, approval, or professional judgment should still
                      be handled by an official advisor.
                    </CardDescription>
                  </CardHeader>
                </Card>
              </div>
            </div>
          </div>
        </section>

        <footer>
          <div className="bg-background px-5 py-3 md:px-8">
            <div className="mx-auto max-w-7xl">
              <Separator className="mb-3" />

              <p className="text-center text-xs text-muted-foreground">
                Owlivia uses generative AI and is not a replacement for an official FAU advisor.
              </p>
            </div>
          </div>
        </footer>
      </div>
    </>
  );
}