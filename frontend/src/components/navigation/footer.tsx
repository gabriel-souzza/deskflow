"use client";

import { usePathname } from "next/navigation";

export function Footer() {
  const pathname = usePathname();
  if (pathname === "/login") return null;

  return (
    <footer className="border-t border-slate-200 bg-white py-6 text-center text-xs font-medium text-slate-500">
      DeskFlow &copy; {new Date().getFullYear()} — Plataforma Corporativa de Espaços Híbridos
    </footer>
  );
}

