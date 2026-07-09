import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import Link from "next/link"

const SignInForm = ({
  triggerText,
  triggerClassName,
  triggerIcon,
}) => (
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

      <div className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="email">Email</Label>
          <Input id="email" placeholder="you@example.com" type="email" />
        </div>

        <div className="space-y-2">
          <Label htmlFor="password">Password</Label>
          <Input id="password" type="password" />
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Checkbox id="remember" />
            <Label className="font-normal text-sm" htmlFor="remember">
              Remember me
            </Label>
          </div>

          <button className="font-medium text-sm underline" type="button">
            Forgot password?
          </button>
        </div>
      </div>

    <DialogFooter>
        <Button asChild className="w-full">
            <Link href="/chat">
            Sign In
            </Link>
        </Button>
    </DialogFooter>

      <p className="text-center text-muted-foreground text-sm">
        Don't have an account?&nbsp;
        <button className="font-medium underline" type="button">
          Sign up
        </button>
      </p>
    </DialogContent>
  </Dialog>
)

export default SignInForm