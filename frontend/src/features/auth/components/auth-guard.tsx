"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useCurrentUser } from "@/features/auth/hooks/use-auth";
import { Building2, Loader2 } from "lucide-react";

interface AuthGuardProps {
  children: React.ReactNode;
}

export function AuthGuard({ children }: AuthGuardProps) {
  const pathname = usePathname();
  const router = useRouter();
  const [mounted, setMounted] = useState(false);
  const { data: user, isLoading } = useCurrentUser();

  useEffect(() => {
    setMounted(true);
  }, []);

  const isLoginPage = pathname === "/login";

  useEffect(() => {
    if (!mounted || isLoading) return;

    if (!user && !isLoginPage) {
      router.replace("/login");
    } else if (user && isLoginPage) {
      router.replace("/");
    }
  }, [mounted, isLoading, user, isLoginPage, router]);

  // Durante a montagem no cliente (SSR e primeiro ciclo de hidratação)
  if (!mounted) {
    if (isLoginPage) {
      return <>{children}</>;
    }
    return (
      <div className="min-h-[70vh] flex flex-col items-center justify-center p-8 text-center">
        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-blue-600 text-white shadow-md shadow-blue-500/25 mb-4 animate-pulse">
          <Building2 className="h-6 w-6" />
        </div>
        <div className="h-4 w-36 bg-slate-200 rounded animate-pulse" />
      </div>
    );
  }

  // Na página de login
  if (isLoginPage) {
    if (user) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-slate-100">
          <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
        </div>
      );
    }
    return <>{children}</>;
  }

  // Nas páginas internas: enquanto carrega ou se não estiver autenticado (aguardando redirect)
  if (isLoading || !user) {
    return (
      <div className="min-h-[70vh] flex flex-col items-center justify-center p-8 text-center">
        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-blue-600 text-white shadow-md shadow-blue-500/25 mb-4">
          <Building2 className="h-6 w-6" />
        </div>
        <div className="flex items-center gap-2 text-sm text-slate-500 font-medium">
          <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
          <span>Verificando credenciais de acesso corporativo...</span>
        </div>
      </div>
    );
  }

  // Usuário autenticado com acesso liberado à página interna
  return <>{children}</>;
}

