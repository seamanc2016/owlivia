"use client"

import * as React from "react"
import { MessageSquare } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import SignInForm from "./sign-in-form"

export const Hero = React.forwardRef(
  (
    {
      className,
      title,
      description,
      buttonText,
      mobileImage,
      desktopBackgroundImage,
      onButtonClick,
      ...props
    },
    ref
  ) => {
    return (
      <section
        ref={ref}
        className={cn(
          "relative min-h-[calc(100vh-4rem)] w-full overflow-hidden bg-secondary",
          className
        )}
        {...props}
      >
        {/* Desktop background image: lg and up */}
        <div
          className="absolute inset-0 hidden bg-cover bg-[position:center_35%] bg-no-repeat lg:block"
          style={{
            backgroundImage: `url(${desktopBackgroundImage})`,
          }}
        />

        <div className="container relative z-10 mx-auto flex min-h-[calc(100vh-4rem)] max-w-screen-2xl items-center justify-center px-4 md:px-6 lg:justify-start lg:px-24">
          <div className="flex w-full max-w-md flex-col items-center text-center sm:max-w-lg md:max-w-2xl lg:max-w-xl lg:items-start lg:text-left">
            {/* Mobile/tablet image: below lg */}
            <img
              src={mobileImage}
              alt="Owlivia"
              className="mb-6 block w-64 sm:w-80 md:w-[28rem] lg:hidden"
            />

            <h1 className="whitespace-pre-line font-serif text-5xl leading-none text-primary sm:text-6xl md:text-7xl lg:text-8xl xl:text-9xl">
              {title}
            </h1>

            <p className="mt-6 max-w-sm text-sm leading-7 text-foreground sm:max-w-md md:max-w-lg md:text-base lg:max-w-md">
              {description}
            </p>

            <SignInForm
              triggerText={buttonText}
              triggerClassName="mt-8 w-full max-w-sm bg-primary hover:bg-primary/90 sm:max-w-md md:max-w-lg lg:max-w-md"
              triggerIcon={<MessageSquare className="size-4" />}
            />
          </div>
        </div>
      </section>
    )
  }
)

Hero.displayName = "Hero"