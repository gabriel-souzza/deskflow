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
  Menu,
  Shield,
  User,
  X,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useCurrentUser, useLogout } from "@/features/auth/hooks/use-auth";
import { cn } from "@/lib/utils";

export function Navbar() {
  const pathname = usePathname();
  const [mounted, setMounted] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { data: user, isLoading } = useCurrentUser();
  const logout = useLogout();

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    setMobileMenuOpen(false);
  }, [pathname]);

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
                      ? "bg-blue-50 text-blue-700 font-bold"
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

        <div className="flex items-center gap-2">
          {!mounted || isLoading ? (
            <div className="h-8 w-24 animate-pulse rounded-md bg-slate-100" />
          ) : user ? (
            <div className="flex items-center gap-2 sm:gap-3">
              <div className="hidden sm:flex flex-col text-right">
                <span className="text-sm font-semibold text-slate-800">{user.name}</span>
                <span className="text-xs font-medium text-slate-500">
                  {user.costCenterName || "Sem Centro"} &bull;{" "}
                  {user.isEligibleForBooking ? "Elegível" : "Sem Ponto"}
                </span>
              </div>
              <Badge variant={user.isAdmin() ? "default" : "secondary"} className="hidden sm:inline-flex">
                {user.role.toUpperCase()}
              </Badge>
              <Button
                variant="ghost"
                size="icon"
                onClick={logout}
                title="Sair"
                aria-label="Sair"
                className="hidden sm:flex"
              >
                <LogOut className="h-4 w-4 text-slate-500" />
              </Button>
            </div>
          ) : (
            <Link href="/login" className="hidden sm:block">
              <Button size="sm">
                <User className="mr-1.5 h-4 w-4" />
                Entrar
              </Button>
            </Link>
          )}

          {/* Botão de Menu Hambúrguer para Mobile */}
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden text-slate-700 hover:bg-slate-100"
            aria-label={mobileMenuOpen ? "Fechar menu" : "Abrir menu"}
          >
            {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </Button>
        </div>
      </div>

      {/* Menu Drawer / Dropdown Mobile */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-slate-200 bg-white px-4 py-3 space-y-1.5 shadow-lg animate-in slide-in-from-top-2 duration-150">
          {user && (
            <div className="flex items-center justify-between pb-3 mb-2 border-b border-slate-100 px-2 pt-1">
              <div>
                <div className="font-bold text-sm text-slate-900">{user.name}</div>
                <div className="text-xs text-slate-500">
                  {user.costCenterName || "Sem Centro"} &bull;{" "}
                  {user.isEligibleForBooking ? "Elegível" : "Sem Ponto"}
                </div>
              </div>
              <Badge variant={user.isAdmin() ? "default" : "secondary"}>
                {user.role.toUpperCase()}
              </Badge>
            </div>
          )}

          <nav className="flex flex-col space-y-1">
            {navLinks.map((link) => {
              const Icon = link.icon;
              const isActive = pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className={cn(
                    "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-semibold transition-colors",
                    isActive
                      ? "bg-blue-50 text-blue-700 font-bold"
                      : "text-slate-700 hover:bg-slate-100 hover:text-slate-900"
                  )}
                >
                  <Icon className="h-5 w-5 shrink-0 text-blue-600" />
                  <span>{link.label}</span>
                </Link>
              );
            })}
          </nav>

          {user ? (
            <div className="pt-2 border-t border-slate-100">
              <button
                type="button"
                onClick={() => {
                  setMobileMenuOpen(false);
                  logout();
                }}
                className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-semibold text-red-600 hover:bg-red-50 transition-colors"
              >
                <LogOut className="h-5 w-5 shrink-0" />
                <span>Sair da Conta</span>
              </button>
            </div>
          ) : (
            <div className="pt-2 border-t border-slate-100">
              <Link
                href="/login"
                onClick={() => setMobileMenuOpen(false)}
                className="flex w-full items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-xs hover:bg-blue-700 transition-colors"
              >
                <User className="h-4 w-4" />
                <span>Entrar no DeskFlow</span>
              </Link>
            </div>
          )}
        </div>
      )}
    </header>
  );
}

