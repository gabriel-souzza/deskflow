"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  AlertCircle,
  ArrowRight,
  Building2,
  Check,
  Eye,
  EyeOff,
  HelpCircle,
  Loader2,
  Lock,
  Mail,
  ShieldCheck,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { useLogin } from "@/features/auth/hooks/use-auth";

interface DemoAccount {
  id: "ana" | "carlos";
  name: string;
  email: string;
  pass: string;
  role: "Colaborador" | "Admin";
  roleVariant: "secondary" | "default";
  initials: string;
}

const DEMO_ACCOUNTS: DemoAccount[] = [
  {
    id: "ana",
    name: "Ana Silva",
    email: "ana.silva@deskflow.com",
    pass: "Colab123456!",
    role: "Colaborador",
    roleVariant: "secondary",
    initials: "AS",
  },
  {
    id: "carlos",
    name: "Carlos Mendes",
    email: "carlos.admin@deskflow.com",
    pass: "Admin123456!",
    role: "Admin",
    roleVariant: "default",
    initials: "CM",
  },
];

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [activePersona, setActivePersona] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isForgotPasswordOpen, setIsForgotPasswordOpen] = useState(false);

  const loginMutation = useLogin();

  useEffect(() => {
    try {
      const savedEmail = localStorage.getItem("deskflow_remembered_email");
      if (savedEmail) {
        setEmail(savedEmail);
        setRememberMe(true);
      }
    } catch {
      // Ignore localStorage errors
    }
  }, []);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    try {
      await loginMutation.mutateAsync({ username: email, password });

      if (rememberMe) {
        localStorage.setItem("deskflow_remembered_email", email);
      } else {
        localStorage.removeItem("deskflow_remembered_email");
      }

      router.push("/");
      router.refresh();
    } catch (err) {
      if (err instanceof Error) {
        setErrorMessage(err.message || "Credenciais inválidas. Verifique seu e-mail e senha.");
      } else {
        setErrorMessage("Erro ao conectar ao servidor. Tente novamente mais tarde.");
      }
    }
  };

  const handleSelectDemo = (account: DemoAccount) => {
    setEmail(account.email);
    setPassword(account.pass);
    setActivePersona(account.id);
    setErrorMessage(null);
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-slate-100 p-4 relative">
      {/* Padrão sutil e limpo de fundo */}
      <div className="absolute inset-0 bg-[radial-gradient(#cbd5e1_1px,transparent_1px)] [background-size:20px_20px] opacity-70 pointer-events-none" />

      {/* Card Centralizado com Alto Contraste (Light Mode) */}
      <div className="relative z-10 w-full max-w-[420px] bg-white rounded-2xl border border-slate-200 shadow-xl shadow-slate-300/40 p-6 sm:p-8 space-y-6">
        
        {/* Cabeçalho */}
        <div className="text-center space-y-2">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-blue-600 text-white shadow-md shadow-blue-500/25">
            <Building2 className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">
              DeskFlow
            </h1>
            <p className="text-xs font-medium text-slate-500 mt-0.5">
              Gestão de Espaços Híbridos
            </p>
          </div>
        </div>

        {/* Acesso Rápido de Teste */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-600">
              Acesso Rápido de Teste
            </span>
            <span className="text-[11px] text-blue-600 font-semibold">
              1 clique para preencher
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2.5">
            {DEMO_ACCOUNTS.map((account) => {
              const isSelected = activePersona === account.id;
              return (
                <button
                  key={account.id}
                  type="button"
                  onClick={() => handleSelectDemo(account)}
                  className={`flex items-center gap-2 p-2.5 rounded-xl border text-left transition-all cursor-pointer ${
                    isSelected
                      ? "border-blue-600 bg-blue-50/80 ring-2 ring-blue-500/20 shadow-xs"
                      : "border-slate-200 hover:border-slate-300 hover:bg-slate-50 bg-white"
                  }`}
                >
                  <div
                    className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-xs font-bold ${
                      account.id === "ana"
                        ? "bg-blue-100 text-blue-700"
                        : "bg-indigo-100 text-indigo-700"
                    }`}
                  >
                    {account.initials}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-900 truncate">
                        {account.name}
                      </span>
                      {isSelected && <Check className="h-3.5 w-3.5 text-blue-600 shrink-0" />}
                    </div>
                    <Badge variant={account.roleVariant} className="text-[10px] px-1.5 py-0 h-4 mt-0.5 font-semibold">
                      {account.role}
                    </Badge>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Divisor Visual */}
        <div className="relative">
          <div className="absolute inset-0 flex items-center">
            <span className="w-full border-t border-slate-200" />
          </div>
          <div className="relative flex justify-center text-[11px] uppercase">
            <span className="bg-white px-3 text-slate-500 font-semibold tracking-wider">
              Ou entre com suas credenciais
            </span>
          </div>
        </div>

        {/* Alerta de Erro */}
        {errorMessage && (
          <div className="rounded-xl border border-red-200 bg-red-50 p-3 text-xs text-red-800 flex items-center gap-2 shadow-xs">
            <AlertCircle className="h-4 w-4 shrink-0 text-red-600" />
            <span className="flex-1 font-medium">{errorMessage}</span>
          </div>
        )}

        {/* Formulário com Alto Contraste */}
        <form onSubmit={handleLogin} className="space-y-4">
          <div className="space-y-1.5">
            <label
              htmlFor="email"
              className="text-xs font-bold uppercase tracking-wider text-slate-800"
            >
              E-mail Corporativo
            </label>
            <div className="relative">
              <Mail className="absolute left-3 top-3 h-4 w-4 text-slate-500 pointer-events-none" />
              <Input
                id="email"
                type="email"
                placeholder="colaborador@deskflow.com"
                autoComplete="email"
                className="pl-9 h-10 text-sm font-semibold text-slate-900 bg-white border-slate-300 placeholder:text-slate-400 focus:border-blue-600 focus:ring-2 focus:ring-blue-100"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  setActivePersona(null);
                }}
                required
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <label
                htmlFor="password"
                className="text-xs font-bold uppercase tracking-wider text-slate-800"
              >
                Senha de Acesso
              </label>
              <button
                type="button"
                onClick={() => setIsForgotPasswordOpen(true)}
                className="text-xs font-semibold text-blue-600 hover:text-blue-800 hover:underline cursor-pointer"
              >
                Esqueceu a senha?
              </button>
            </div>
            <div className="relative">
              <Lock className="absolute left-3 top-3 h-4 w-4 text-slate-500 pointer-events-none" />
              <Input
                id="password"
                type={showPassword ? "text" : "password"}
                placeholder="••••••••••••"
                autoComplete="current-password"
                className="pl-9 pr-10 h-10 text-sm font-semibold text-slate-900 bg-white border-slate-300 placeholder:text-slate-400 focus:border-blue-600 focus:ring-2 focus:ring-blue-100"
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  setActivePersona(null);
                }}
                required
              />
              <button
                type="button"
                aria-label="Alternar visibilidade da senha"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-3 text-slate-500 hover:text-slate-700 cursor-pointer p-0.5"
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>

          <div className="flex items-center justify-between pt-0.5">
            <label className="flex items-center gap-2 cursor-pointer text-xs font-medium text-slate-700 select-none">
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                className="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
              />
              <span>Lembrar meu e-mail neste navegador</span>
            </label>
          </div>

          <Button
            type="submit"
            className="w-full h-11 text-sm font-bold bg-blue-600 hover:bg-blue-700 text-white shadow-md shadow-blue-600/20 cursor-pointer flex items-center justify-center gap-2 transition-all"
            disabled={loginMutation.isPending}
          >
            {loginMutation.isPending ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Entrando...</span>
              </>
            ) : (
              <>
                <span>Acessar Plataforma</span>
                <ArrowRight className="h-4 w-4" />
              </>
            )}
          </Button>
        </form>

        {/* Rodapé Discreto */}
        <div className="pt-2 text-center border-t border-slate-100">
          <p className="text-[11px] font-medium text-slate-500 flex items-center justify-center gap-1.5">
            <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />
            <span>Ambiente seguro com criptografia de ponta a ponta</span>
          </p>
        </div>
      </div>

      {/* Modal: Esqueceu a Senha */}
      <Dialog open={isForgotPasswordOpen} onOpenChange={setIsForgotPasswordOpen}>
        <DialogContent className="sm:max-w-sm bg-white">
          <DialogHeader>
            <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-full bg-blue-50 text-blue-600 mb-1">
              <HelpCircle className="h-5 w-5" />
            </div>
            <DialogTitle className="text-center text-base font-bold text-slate-900">
              Redefinição de Senha
            </DialogTitle>
            <DialogDescription className="text-center text-xs text-slate-600 pt-2 space-y-2">
              <p>
                Por políticas corporativas, a redefinição de senhas é realizada pelo administrador da plataforma ou gestor do seu centro de custo.
              </p>
              <p className="text-[11px] bg-slate-100 p-2.5 rounded-lg text-slate-800 text-left font-medium">
                Se você é um administrador, use a aba <em>Painel Admin &gt; Colaboradores</em> para atualizar senhas de colaboradores.
              </p>
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="sm:justify-center">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setIsForgotPasswordOpen(false)}
            >
              Fechar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
