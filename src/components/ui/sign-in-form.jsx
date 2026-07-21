"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { AlertCircle } from "lucide-react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const SignInForm = ({ triggerText, triggerClassName, triggerIcon }) => {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  const handleSubmit = (event) => {
    event.preventDefault();

    const trimmedEmail = email.trim();

    // Both fields are required
    if (!trimmedEmail || !password) {
      setErrorMessage("Please enter both your FAU email and password.");
      return;
    }

    // Email must be a valid @fau.edu address
    const isValidFauEmail = /^[^\s@]+@fau\.edu$/i.test(trimmedEmail);

    if (!isValidFauEmail) {
      setErrorMessage("Please enter a valid email address ending in @fau.edu.");
      return;
    }

    setErrorMessage("");

    // Replace with auth request later if implemented
    router.push("/chat");
  };

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button className={triggerClassName}>
          {triggerIcon && <span className="mr-2">{triggerIcon}</span>}
          {triggerText}
        </Button>
      </DialogTrigger>

      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Welcome back</DialogTitle>
          <DialogDescription>
            Enter your credentials to access your account.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} noValidate>
          <div className="space-y-4">
            {errorMessage && (
              <Alert variant="destructive">
                <AlertCircle />
                <AlertDescription>{errorMessage}</AlertDescription>
              </Alert>
            )}

            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                name="email"
                placeholder="student@fau.edu"
                type="email"
                value={email}
                onChange={(event) => {
                  setEmail(event.target.value);

                  if (errorMessage) {
                    setErrorMessage("");
                  }
                }}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                name="password"
                type="password"
                value={password}
                onChange={(event) => {
                  setPassword(event.target.value);

                  if (errorMessage) {
                    setErrorMessage("");
                  }
                }}
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Checkbox id="remember" />
                <Label className="font-normal text-sm" htmlFor="remember">
                  Remember me
                </Label>
              </div>

              <button className="font-medium text-sm underline" type="button">
                <a href="https://accounts.iam.fau.edu/reset.html" target="_blank">Forgot password?</a>
              </button>
            </div>
          </div>

          <DialogFooter className="mt-6">
            <Button className="w-full" type="submit">
              Sign In
            </Button>
          </DialogFooter>
        </form>

        {/* <p className="text-center text-muted-foreground text-sm">
          Don&apos;t have an account?&nbsp;
          <button className="font-medium underline" type="button">
            Sign up
          </button>
        </p> */}
      </DialogContent>
    </Dialog>
  );
};

export default SignInForm;
