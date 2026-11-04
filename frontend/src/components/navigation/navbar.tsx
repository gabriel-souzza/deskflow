"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Building2,
  CalendarDays,
  Clock,
  LayoutDashboard,
  LogOut,
  Shield,
  User,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useCurrentUser, useLogout } from "@/features/auth/hooks/use-auth";
import { cn } from "@/lib/utils";

export function Navbar() {
  const pathname = usePathname();
  const [mounted, setMounted] = useState(false);
  const { data: user, isLoading } = useCurrentUser();
  const logout = useLogout();

  useEffect(() => {
    setMounted(true);
  }, []);

  if (pathname === "/login") return null;

  const navLinks = [
    { href: "/", label: "Espaços", icon: Building2 },
    { href: "/my-bookings", label: "Minhas Reservas", icon: CalendarDays },
    { href: "/waitlist", label: "Fila de Espera", icon: Clock },
    { href: "/reports", label: "Relatórios", icon: LayoutDashboard },
  ];

  if (mounted && user?.isAdmin()) {
    navLinks.push({ href: "/admin", label: "Administração", icon: Shield });
  }

  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-200 bg-white/95 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-8">
          <Link href="/" className="flex items-center gap-2 font-bold text-xl text-blue-600">
            <Building2 className="h-6 w-6" />
            <span>DeskFlow</span>
          </Link>

          <nav className="hidden md:flex items-center gap-1">
            {navLinks.map((link) => {
              const Icon = link.icon;
              const isActive = pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={cn(
                    "flex items-center gap-1.5 rounded-md px-3 py-2 text-sm font-semibold transition-colors",
                    isActive
                      ? "bg-blue-50 text-blue-700"
                      : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                  )}
                >
                  <Icon className="h-4 w-4" />
                  <span>{link.label}</span>
                </Link>
              );
            })}
          </nav>
        </div>

        <div className="flex items-center gap-3">
          {!mounted || isLoading ? (
            <div className="h-8 w-24 animate-pulse rounded-md bg-slate-100" />
          ) : user ? (
            <div className="flex items-center gap-3">
              <div className="hidden sm:flex flex-col text-right">
                <span className="text-sm font-semibold text-slate-800">{user.name}</span>
                <span className="text-xs font-medium text-slate-500">
                  {user.costCenterName || "Sem Centro"} &bull;{" "}
                  {user.isEligibleForBooking ? "Elegível" : "Sem Ponto"}
                </span>
              </div>
              <Badge variant={user.isAdmin() ? "default" : "secondary"}>
                {user.role.toUpperCase()}
              </Badge>
              <Button
                variant="ghost"
                size="icon"
                onClick={logout}
                title="Sair"
                aria-label="Sair"
              >
                <LogOut className="h-4 w-4 text-slate-500" />
              </Button>
            </div>
          ) : (
            <Link href="/login">
              <Button size="sm">
                <User className="mr-1.5 h-4 w-4" />
                Entrar
              </Button>
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}

