import Link from "next/link"
import { LogOut } from "lucide-react"

import { Button } from "@/components/ui/button"

export function ChatNavbar() {
  return (
    <div className="bg-primary text-primary-foreground">
      <div className="mx-auto flex max-w-5xl items-center justify-between p-2">
        <div className="text-xl font-bold">Owlivia</div>

        <Button
          className="bg-destructive hover:bg-primary-foreground hover:text-primary"
          asChild
        >
          <Link href="/">
            <LogOut />
            Logout
          </Link>
        </Button>
      </div>
    </div>
  )
}