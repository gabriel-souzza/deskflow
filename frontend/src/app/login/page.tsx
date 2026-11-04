"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Building2, Lock, Mail } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useLogin } from "@/features/auth/hooks/use-auth";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const loginMutation = useLogin();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    try {
      await loginMutation.mutateAsync({ username: email, password });
      router.push("/");
    } catch (err) {
      if (err instanceof Error) {
        setErrorMessage(err.message || "Credenciais inválidas. Verifique seu email e senha.");
      } else {
        setErrorMessage("Erro ao conectar ao servidor.");
      }
    }
  };

  const handleQuickDemo = (demoEmail: string, demoPass: string) => {
    setEmail(demoEmail);
    setPassword(demoPass);
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 p-4">
      <Card className="w-full max-w-md shadow-xl border-slate-200">
        <CardHeader className="text-center space-y-2">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-blue-100 text-blue-600">
            <Building2 className="h-6 w-6" />
          </div>
          <CardTitle className="text-2xl font-bold tracking-tight text-slate-900">
            DeskFlow
          </CardTitle>
          <CardDescription>
            Entre com suas credenciais corporativas para gerenciar suas reservas.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleLogin} className="space-y-4">
            {errorMessage && (
              <div className="rounded-md bg-red-50 p-3 text-sm text-red-700 border border-red-200">
                {errorMessage}
              </div>
            )}

            <div className="space-y-1.5">
              <label className="text-xs font-semibold uppercase tracking-wider text-slate-700">
                E-mail
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                <Input
                  type="email"
                  placeholder="colaborador@empresa.com"
                  className="pl-9"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold uppercase tracking-wider text-slate-700">
                Senha
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                <Input
                  type="password"
                  placeholder="••••••••••••"
                  className="pl-9"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>
            </div>

            <Button
              type="submit"
              className="w-full"
              disabled={loginMutation.isPending}
            >
              {loginMutation.isPending ? "Entrando..." : "Acessar Plataforma"}
            </Button>
          </form>

          <div className="mt-6 border-t border-slate-100 pt-4 text-center">
            <p className="text-xs text-slate-500 mb-2 font-medium">Contas de Teste:</p>
            <div className="flex gap-2 justify-center">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => handleQuickDemo("ana.silva@deskflow.com", "Colab123456!")}
              >
                Colaborador (Ana)
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => handleQuickDemo("carlos.admin@deskflow.com", "Admin123456!")}
              >
                Administrador
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

