"use client";

import { useEffect, useState } from "react";
import {
  AlertTriangle,
  Building,
  Building2,
  Calendar,
  CheckCircle2,
  Edit2,
  Lock,
  PieChart,
  Plus,
  Shield,
  Trash2,
  UserCheck,
  UserPlus,
  Users,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import {
  AccountApiItem,
  AdminWorkspaceApiItem,
  CostCenterApiItem,
  useAdminAccounts,
  useAdminCostCenters,
  useAdminHolidays,
  useAdminQuotas,
  useAdminWorkspaces,
  useCreateAccount,
  useCreateCostCenter,
  useCreateHoliday,
  useCreateWorkspace,
  useDeleteAccount,
  useDeleteHoliday,
  useDeleteWorkspace,
  useUpdateAccount,
  useUpdateCostCenter,
  useUpdateWorkspace,
} from "@/features/admin/hooks/use-admin";
import { useCurrentUser } from "@/features/auth/hooks/use-auth";

const AVAILABLE_RESOURCES = [
  { id: "monitor_duplo", label: "Monitor Duplo" },
  { id: "tomada_adicional", label: "Tomada Extra" },
  { id: "usb_c", label: "Dock USB-C" },
  { id: "videoconferencia", label: "Videoconferência" },
  { id: "tv_4k", label: "TV 4K" },
  { id: "whiteboard", label: "Quadro Branco" },
];

const RESOURCE_LABELS: Record<string, string> = {
  monitor_duplo: "Monitor Duplo",
  tomada_adicional: "Tomada",
  usb_c: "USB-C",
  videoconferencia: "Videoconferência",
  tv_4k: "TV 4K",
  whiteboard: "Quadro Branco",
};

export default function AdminPage() {
  const { data: user, isLoading: userLoading } = useCurrentUser();
  const [activeTab, setActiveTab] = useState<"quotas" | "workspaces" | "accounts" | "holidays">("quotas");

  const { data: costCenters } = useAdminCostCenters();
  const { data: quotas } = useAdminQuotas();
  const updateCostCenterMutation = useUpdateCostCenter();
  const createCostCenterMutation = useCreateCostCenter();

  const { data: workspaces, isLoading: workspacesLoading } = useAdminWorkspaces();
  const createWorkspaceMutation = useCreateWorkspace();
  const updateWorkspaceMutation = useUpdateWorkspace();
  const deleteWorkspaceMutation = useDeleteWorkspace();

  const { data: accounts } = useAdminAccounts();
  const updateAccountMutation = useUpdateAccount();
  const createAccountMutation = useCreateAccount();
  const deleteAccountMutation = useDeleteAccount();

  const { data: holidays } = useAdminHolidays();
  const createHolidayMutation = useCreateHoliday();
  const deleteHolidayMutation = useDeleteHoliday();

  // Edição de Centro de Custo existente
  const [editingCc, setEditingCc] = useState<CostCenterApiItem | null>(null);
  const [editingCcHours, setEditingCcHours] = useState<number>(0);

  // Criação de Centro de Custo
  const [isCreatingCc, setIsCreatingCc] = useState(false);
  const [newCcName, setNewCcName] = useState("");
  const [newCcHours, setNewCcHours] = useState(160);

  // Edição de Conta existente
  const [editingAcc, setEditingAcc] = useState<AccountApiItem | null>(null);
  const [editingAccRole, setEditingAccRole] = useState<string>("employee");
  const [editingAccEligible, setEditingAccEligible] = useState<boolean>(true);

  // Exclusão de Conta
  const [accountToDelete, setAccountToDelete] = useState<AccountApiItem | null>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Criação de Nova Conta de Colaborador
  const [isCreatingAcc, setIsCreatingAcc] = useState(false);
  const [newAccName, setNewAccName] = useState("");
  const [newAccEmail, setNewAccEmail] = useState("");
  const [newAccPassword, setNewAccPassword] = useState("");
  const [newAccCostCenterId, setNewAccCostCenterId] = useState("");
  const [newAccRole, setNewAccRole] = useState<"employee" | "admin">("employee");
  const [newAccEligible, setNewAccEligible] = useState<boolean>(true);

  // Criação de Feriado
  const [newHolidayDay, setNewHolidayDay] = useState("");
  const [newHolidayDesc, setNewHolidayDesc] = useState("");

  // Gestão de Espaços
  const [isCreatingWs, setIsCreatingWs] = useState(false);
  const [newWsCode, setNewWsCode] = useState("");
  const [newWsFloor, setNewWsFloor] = useState("");
  const [newWsZone, setNewWsZone] = useState("");
  const [newWsType, setNewWsType] = useState<"estacao" | "sala">("estacao");
  const [newWsCapacity, setNewWsCapacity] = useState(1);
  const [newWsResources, setNewWsResources] = useState<string[]>([]);

  const [editingWs, setEditingWs] = useState<AdminWorkspaceApiItem | null>(null);
  const [editWsCode, setEditWsCode] = useState("");
  const [editWsFloor, setEditWsFloor] = useState("");
  const [editWsZone, setEditWsZone] = useState("");
  const [editWsType, setEditWsType] = useState<"estacao" | "sala">("estacao");
  const [editWsCapacity, setEditWsCapacity] = useState(1);
  const [editWsResources, setEditWsResources] = useState<string[]>([]);

  const [wsToDelete, setWsToDelete] = useState<AdminWorkspaceApiItem | null>(null);

  const [feedback, setFeedback] = useState<{ type: "success" | "error"; text: string } | null>(null);

  if (!mounted || userLoading) {
    return (
      <div className="mx-auto max-w-7xl p-8">
        <div className="h-10 w-48 animate-pulse rounded bg-slate-200" />
      </div>
    );
  }

  if (!user?.isAdmin()) {
    return (
      <div className="mx-auto max-w-md py-20 text-center">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-amber-50 text-amber-600 mb-4">
          <Lock className="h-7 w-7" />
        </div>
        <h2 className="text-lg font-bold text-slate-900">Acesso Restrito</h2>
        <p className="mt-1 text-sm text-slate-500">
          Esta área é restrita a administradores do sistema DeskFlow.
        </p>
      </div>
    );
  }

  const handleSaveCc = async () => {
    if (!editingCc) return;
    setFeedback(null);
    try {
      await updateCostCenterMutation.mutateAsync({
        id: editingCc.id,
        name: editingCc.name,
        monthly_quota_hours: Number(editingCcHours),
      });
      setFeedback({ type: "success", text: "Cota do centro de custo atualizada com sucesso!" });
      setEditingCc(null);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Falha ao atualizar centro de custo.";
      setFeedback({ type: "error", text: msg });
    }
  };

  const handleCreateCc = async () => {
    if (!newCcName.trim()) {
      setFeedback({ type: "error", text: "Informe o nome do centro de custo." });
      return;
    }
    setFeedback(null);
    try {
      await createCostCenterMutation.mutateAsync({
        name: newCcName.trim(),
        monthly_quota_hours: Number(newCcHours),
      });
      setFeedback({ type: "success", text: "Centro de custo cadastrado com sucesso!" });
      setIsCreatingCc(false);
      setNewCcName("");
      setNewCcHours(160);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Falha ao criar centro de custo.";
      setFeedback({ type: "error", text: msg });
    }
  };

  const handleSaveAccount = async () => {
    if (!editingAcc) return;
    setFeedback(null);
    try {
      await updateAccountMutation.mutateAsync({
        id: editingAcc.id,
        role: editingAccRole,
        is_eligible_for_booking: editingAccEligible,
      });
      setFeedback({ type: "success", text: "Colaborador atualizado com sucesso!" });
      setEditingAcc(null);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Falha ao atualizar colaborador.";
      setFeedback({ type: "error", text: msg });
    }
  };

  const handleDeleteAccount = async () => {
    if (!accountToDelete) return;
    setFeedback(null);
    try {
      await deleteAccountMutation.mutateAsync(accountToDelete.id);
      setFeedback({
        type: "success",
        text: `Colaborador ${accountToDelete.name} excluído com sucesso do sistema!`,
      });
      setAccountToDelete(null);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Falha ao excluir colaborador.";
      setFeedback({ type: "error", text: msg });
    }
  };

  const handleCreateAccount = async () => {
    if (!newAccName.trim()) {
      setFeedback({ type: "error", text: "O nome do colaborador é obrigatório." });
      return;
    }
    if (!newAccEmail.trim() || !newAccEmail.includes("@")) {
      setFeedback({ type: "error", text: "Informe um e-mail corporativo válido." });
      return;
    }
    if (newAccPassword.length < 12) {
      setFeedback({
        type: "error",
        text: "A senha inicial deve conter pelo menos 12 caracteres por segurança (exigência da API).",
      });
      return;
    }
    const ccId = newAccCostCenterId || costCenters?.items?.[0]?.id;
    if (!ccId) {
      setFeedback({ type: "error", text: "Selecione um centro de custo para vincular o colaborador." });
      return;
    }

    setFeedback(null);
    try {
      await createAccountMutation.mutateAsync({
        name: newAccName.trim(),
        email: newAccEmail.trim().toLowerCase(),
        password: newAccPassword,
        cost_center_id: ccId,
        role: newAccRole,
        is_eligible_for_booking: newAccEligible,
      });
      setFeedback({
        type: "success",
        text: `Conta de ${newAccName} (${newAccEmail}) criada com sucesso no sistema!`,
      });
      setIsCreatingAcc(false);
      setNewAccName("");
      setNewAccEmail("");
      setNewAccPassword("");
      setNewAccCostCenterId("");
      setNewAccRole("employee");
      setNewAccEligible(true);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Falha ao criar conta de colaborador.";
      setFeedback({ type: "error", text: msg });
    }
  };

  const handleCreateHoliday = async () => {
    if (!newHolidayDay) {
      setFeedback({ type: "error", text: "Selecione a data do feriado." });
      return;
    }
    setFeedback(null);
    try {
      await createHolidayMutation.mutateAsync({
        day: newHolidayDay,
        description: newHolidayDesc.trim() || "Feriado",
      });
      setFeedback({ type: "success", text: "Feriado bloqueado com sucesso (janelas liberadas)!" });
      setNewHolidayDay("");
      setNewHolidayDesc("");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Falha ao bloquear feriado.";
      setFeedback({ type: "error", text: msg });
    }
  };

  const handleDeleteHoliday = async (day: string) => {
    setFeedback(null);
    try {
      await deleteHolidayMutation.mutateAsync(day);
      setFeedback({ type: "success", text: `Feriado do dia ${day} removido com sucesso!` });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Falha ao remover feriado.";
      setFeedback({ type: "error", text: msg });
    }
  };

  const handleCreateWorkspace = async () => {
    if (!newWsCode.trim()) {
      setFeedback({ type: "error", text: "Informe o código do espaço (ex: EST-101 ou SALA-201)." });
      return;
    }
    if (!newWsFloor.trim()) {
      setFeedback({ type: "error", text: "Informe o andar do espaço (ex: 1º Andar)." });
      return;
    }
    if (!newWsZone.trim()) {
      setFeedback({ type: "error", text: "Informe a zona ou ala do espaço (ex: Ala Norte)." });
      return;
    }
    const capacity = newWsType === "estacao" ? 1 : Math.max(1, newWsCapacity);

    setFeedback(null);
    try {
      await createWorkspaceMutation.mutateAsync({
        code: newWsCode.trim().toUpperCase(),
        floor: newWsFloor.trim(),
        zone: newWsZone.trim(),
        type: newWsType,
        capacity,
        resources: newWsResources,
      });
      setFeedback({
        type: "success",
        text: `Espaço ${newWsCode.trim().toUpperCase()} cadastrado com sucesso!`,
      });
      setIsCreatingWs(false);
      setNewWsCode("");
      setNewWsFloor("");
      setNewWsZone("");
      setNewWsType("estacao");
      setNewWsCapacity(1);
      setNewWsResources([]);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Falha ao criar espaço.";
      setFeedback({ type: "error", text: msg });
    }
  };

  const handleOpenEditWs = (ws: AdminWorkspaceApiItem) => {
    setEditingWs(ws);
    setEditWsCode(ws.code);
    setEditWsFloor(ws.floor);
    setEditWsZone(ws.zone);
    setEditWsType(ws.type);
    setEditWsCapacity(ws.capacity);
    setEditWsResources(Array.isArray(ws.resources) ? ws.resources : []);
  };

  const handleSaveWorkspace = async () => {
    if (!editingWs) return;
    if (!editWsCode.trim()) {
      setFeedback({ type: "error", text: "Informe o código do espaço." });
      return;
    }
    const capacity = editWsType === "estacao" ? 1 : Math.max(1, editWsCapacity);

    setFeedback(null);
    try {
      await updateWorkspaceMutation.mutateAsync({
        id: editingWs.id,
        code: editWsCode.trim().toUpperCase(),
        floor: editWsFloor.trim(),
        zone: editWsZone.trim(),
        type: editWsType,
        capacity,
        resources: editWsResources,
      });
      setFeedback({
        type: "success",
        text: `Espaço ${editWsCode.trim().toUpperCase()} atualizado com sucesso!`,
      });
      setEditingWs(null);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Falha ao atualizar espaço.";
      setFeedback({ type: "error", text: msg });
    }
  };

  const handleDeleteWorkspace = async () => {
    if (!wsToDelete) return;
    setFeedback(null);
    try {
      await deleteWorkspaceMutation.mutateAsync(wsToDelete.id);
      setFeedback({ type: "success", text: `Espaço ${wsToDelete.code} excluído com sucesso!` });
      setWsToDelete(null);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Falha ao excluir espaço.";
      setFeedback({ type: "error", text: msg });
    }
  };

  const criticalQuotas = (quotas?.items ?? [])
    .map((q) => {
      const cc = costCenters?.items?.find((c) => c.id === q.cost_center_id);
      const total = cc?.monthly_quota_hours ?? q.monthly_quota_hours ?? 0;
      const used = q.used_hours;
      const pct = total > 0 ? (used / total) * 100 : 0;
      return {
        ...q,
        name: cc?.name ?? `Centro de Custo`,
        total,
        used,
        pct,
        isCritical: pct >= 95,
        isWarning: pct >= 80 && pct < 95,
      };
    })
    .filter((item) => item.isCritical || item.isWarning);

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="border-b border-slate-200 pb-5">
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
          <Shield className="h-6 w-6 text-blue-600" />
          Painel de Administração
        </h1>
        <p className="text-sm font-medium text-slate-600 mt-1">
          Configuração de cotas por centro de custo, gestão de espaços e salas, contas de colaboradores e controle de feriados.
        </p>
      </div>

      {feedback && (
        <div
          className={`mt-4 rounded-lg p-3.5 text-sm font-medium border flex items-center gap-2.5 ${
            feedback.type === "success"
              ? "bg-emerald-50 text-emerald-800 border-emerald-200"
              : "bg-red-50 text-red-800 border-red-200"
          }`}
        >
          {feedback.type === "success" ? (
            <CheckCircle2 className="h-5 w-5 shrink-0 text-emerald-600" />
          ) : (
            <AlertTriangle className="h-5 w-5 shrink-0 text-red-600" />
          )}
          <span>{feedback.text}</span>
        </div>
      )}

      <div className="mt-6 flex border-b border-slate-200 space-x-6 overflow-x-auto">
        <button
          onClick={() => setActiveTab("quotas")}
          className={`pb-3 text-sm font-semibold border-b-2 transition-colors flex items-center gap-2 shrink-0 ${
            activeTab === "quotas"
              ? "border-blue-600 text-blue-600"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          <PieChart className="h-4 w-4" />
          Cotas & Centros de Custo
        </button>

        <button
          onClick={() => setActiveTab("workspaces")}
          className={`pb-3 text-sm font-semibold border-b-2 transition-colors flex items-center gap-2 shrink-0 ${
            activeTab === "workspaces"
              ? "border-blue-600 text-blue-600"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          <Building2 className="h-4 w-4" />
          Espaços & Estações
        </button>

        <button
          onClick={() => setActiveTab("accounts")}
          className={`pb-3 text-sm font-semibold border-b-2 transition-colors flex items-center gap-2 shrink-0 ${
            activeTab === "accounts"
              ? "border-blue-600 text-blue-600"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          <Users className="h-4 w-4" />
          Contas & Elegibilidade
        </button>

        <button
          onClick={() => setActiveTab("holidays")}
          className={`pb-3 text-sm font-semibold border-b-2 transition-colors flex items-center gap-2 shrink-0 ${
            activeTab === "holidays"
              ? "border-blue-600 text-blue-600"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          <Building className="h-4 w-4" />
          Feriados & Bloqueios
        </button>
      </div>

      {activeTab === "quotas" && (
        <div className="mt-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-bold text-slate-900">Centros de Custo & Cotas Mensais</h2>
              <p className="text-xs text-slate-600">
                Acompanhamento de horas reservadas e alertas automáticos de consumo de 80% e 95%.
              </p>
            </div>
            <Button
              size="sm"
              onClick={() => setIsCreatingCc(true)}
              className="gap-1.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs"
            >
              <Plus className="h-4 w-4" />
              Novo Centro de Custo
            </Button>
          </div>

          {criticalQuotas.length > 0 && (
            <div className="rounded-xl border border-amber-300 bg-amber-50/90 p-4 shadow-xs">
              <div className="flex items-start gap-3">
                <AlertTriangle className="h-5 w-5 text-amber-600 shrink-0 mt-0.5" />
                <div className="space-y-2 flex-1">
                  <div>
                    <h3 className="text-sm font-bold text-amber-950">
                      Alerta de Cota Crítica — Acompanhamento de Rateio Corporativo
                    </h3>
                    <p className="text-xs text-amber-800 mt-0.5">
                      Centros de custo com alto consumo mensal de horas. Em 80% o gestor é alertado; ao atingir 95%, novas reservas são bloqueadas preventivamente.
                    </p>
                  </div>
                  <div className="space-y-2">
                    {criticalQuotas.map((cq) => (
                      <div
                        key={cq.cost_center_id}
                        className={`flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 rounded-lg p-2.5 text-xs border ${
                          cq.isCritical
                            ? "bg-red-50 text-red-950 border-red-200"
                            : "bg-amber-100/70 text-amber-950 border-amber-300"
                        }`}
                      >
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="font-bold text-slate-900">{cq.name}</span>
                          <span className="text-slate-700">
                            {cq.used}h de {cq.total}h utilizadas ({cq.pct.toFixed(1)}%)
                          </span>
                          <Badge
                            variant={cq.isCritical ? "destructive" : "warning"}
                            className="text-[10px] py-0 px-1.5 font-bold"
                          >
                            {cq.isCritical ? "CRÍTICO 95%" : "ALERTA 80%"}
                          </Badge>
                        </div>
                        <Button
                          size="sm"
                          variant="outline"
                          className="h-7 text-xs bg-white hover:bg-slate-50 border-slate-300 font-semibold shrink-0"
                          onClick={() => {
                            const cc = costCenters?.items?.find((c) => c.id === cq.cost_center_id);
                            if (cc) {
                              setEditingCc(cc);
                              setEditingCcHours(cc.monthly_quota_hours);
                            }
                          }}
                        >
                          Ajustar Cota
                        </Button>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {costCenters?.items?.map((cc) => {
              const q = quotas?.items?.find((q) => q.cost_center_id === cc.id);
              const usedHours = q?.used_hours ?? 0;
              const totalHours = cc.monthly_quota_hours;
              const percent = totalHours > 0 ? (usedHours / totalHours) * 100 : 0;
              const isAlert95 = percent >= 95;
              const isAlert80 = percent >= 80 && percent < 95;

              return (
                <Card key={cc.id} className="shadow-xs border-slate-200 bg-white">
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-base font-bold text-slate-900">
                        {cc.name}
                      </CardTitle>
                      {isAlert95 && <Badge variant="destructive">Alerta 95%</Badge>}
                      {isAlert80 && <Badge variant="warning">Alerta 80%</Badge>}
                      {!isAlert80 && !isAlert95 && (
                        <span className="inline-flex items-center rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-semibold text-slate-700 border border-slate-200">
                          Normal
                        </span>
                      )}
                    </div>
                    <CardDescription className="text-xs font-medium text-slate-600">
                      Consumo do mês: {usedHours}h de {totalHours}h ({percent.toFixed(1)}%)
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="pt-0 pb-4">
                    <div className="w-full bg-slate-100 rounded-full h-2 mb-3">
                      <div
                        className={`h-2 rounded-full ${
                          isAlert95
                            ? "bg-red-500"
                            : isAlert80
                            ? "bg-amber-500"
                            : "bg-blue-600"
                        }`}
                        style={{ width: `${Math.min(100, percent)}%` }}
                      />
                    </div>

                    {editingCc?.id === cc.id ? (
                      <div className="flex items-center gap-2 pt-2">
                        <Input
                          type="number"
                          value={editingCcHours}
                          onChange={(e) => setEditingCcHours(Number(e.target.value))}
                          className="w-28 text-sm"
                        />
                        <Button size="sm" onClick={handleSaveCc}>
                          Salvar
                        </Button>
                        <Button size="sm" variant="ghost" onClick={() => setEditingCc(null)}>
                          Cancelar
                        </Button>
                      </div>
                    ) : (
                      <div className="flex justify-end pt-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            setEditingCc(cc);
                            setEditingCcHours(cc.monthly_quota_hours);
                          }}
                        >
                          Alterar Cota Mensal
                        </Button>
                      </div>
                    )}
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      )}

      {activeTab === "workspaces" && (
        <div className="mt-6 space-y-4">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-base font-bold text-slate-900">Espaços & Estações de Trabalho</h2>
              <p className="text-xs text-slate-600">
                Cadastre, configure recursos (monitores, tomadas, videoconferência) e gerencie a capacidade das estações e salas.
              </p>
            </div>
            <Button
              size="sm"
              onClick={() => {
                setNewWsCode("");
                setNewWsFloor("");
                setNewWsZone("");
                setNewWsType("estacao");
                setNewWsCapacity(1);
                setNewWsResources([]);
                setIsCreatingWs(true);
              }}
              className="gap-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs shadow-xs"
            >
              <Plus className="h-4 w-4" />
              Novo Espaço
            </Button>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white overflow-hidden shadow-xs">
            {workspacesLoading ? (
              <div className="p-8 text-center text-sm text-slate-500">Carregando espaços...</div>
            ) : !workspaces?.items || workspaces.items.length === 0 ? (
              <div className="p-8 text-center text-sm text-slate-500">Nenhum espaço cadastrado ainda.</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm text-slate-700">
                  <thead className="bg-slate-50 text-xs font-bold uppercase text-slate-600 border-b border-slate-200">
                    <tr>
                      <th className="px-4 py-3">Código</th>
                      <th className="px-4 py-3">Tipo</th>
                      <th className="px-4 py-3">Localização</th>
                      <th className="px-4 py-3">Capacidade</th>
                      <th className="px-4 py-3">Recursos Disponíveis</th>
                      <th className="px-4 py-3 text-right">Ações</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {workspaces.items.map((ws) => {
                      const wsResList = Array.isArray(ws.resources) ? ws.resources : [];
                      return (
                        <tr key={ws.id} className="hover:bg-slate-50/70 transition-colors">
                          <td className="px-4 py-3 font-mono font-bold text-slate-900">
                            {ws.code}
                          </td>
                          <td className="px-4 py-3">
                            <Badge variant={ws.type === "sala" ? "default" : "secondary"}>
                              {ws.type === "sala" ? "Sala de Reunião" : "Estação"}
                            </Badge>
                          </td>
                          <td className="px-4 py-3 text-slate-700 font-medium">
                            {ws.floor} • {ws.zone}
                          </td>
                          <td className="px-4 py-3 text-slate-700 font-medium">
                            {ws.capacity} {ws.capacity === 1 ? "pessoa" : "pessoas"}
                          </td>
                          <td className="px-4 py-3">
                            <div className="flex flex-wrap gap-1">
                              {wsResList.length > 0 ? (
                                wsResList.map((resKey) => (
                                  <span
                                    key={resKey}
                                    className="inline-flex items-center px-1.5 py-0.5 rounded text-[11px] font-medium bg-slate-100 text-slate-700 border border-slate-200"
                                  >
                                    {RESOURCE_LABELS[resKey] || resKey}
                                  </span>
                                ))
                              ) : (
                                <span className="text-xs text-slate-400">Padrão</span>
                              )}
                            </div>
                          </td>
                          <td className="px-4 py-3 text-right">
                            <div className="flex items-center justify-end gap-1">
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => handleOpenEditWs(ws)}
                                className="text-xs font-medium text-slate-600 hover:text-slate-900 h-8 px-2"
                                title="Editar espaço"
                              >
                                <Edit2 className="h-4 w-4 mr-1 text-slate-500" />
                                Editar
                              </Button>
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => setWsToDelete(ws)}
                                className="text-red-600 hover:text-red-700 hover:bg-red-50 h-8 w-8 p-0"
                                title="Excluir espaço"
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === "accounts" && (
        <div className="mt-6 space-y-4">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-base font-bold text-slate-900">Colaboradores Cadastrados</h2>
              <p className="text-xs text-slate-600">
                Gerencie contas, níveis de privilégio (Admin/Colaborador) e status de elegibilidade por frequência híbrida.
              </p>
            </div>
            <Button
              size="sm"
              onClick={() => setIsCreatingAcc(true)}
              className="gap-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs shadow-xs"
            >
              <UserPlus className="h-4 w-4" />
              Novo Colaborador
            </Button>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white overflow-hidden shadow-xs">
            <table className="w-full text-left text-sm text-slate-700">
              <thead className="bg-slate-50 text-xs font-bold uppercase text-slate-600 border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3">Nome & E-mail</th>
                  <th className="px-4 py-3">Centro de Custo</th>
                  <th className="px-4 py-3">Papel</th>
                  <th className="px-4 py-3">Elegibilidade</th>
                  <th className="px-4 py-3 text-right">Ação</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {accounts?.items?.map((acc) => (
                  <tr key={acc.id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="px-4 py-3">
                      <div className="font-bold text-slate-900">{acc.name}</div>
                      <div className="text-xs font-medium text-slate-500">{acc.email}</div>
                    </td>
                    <td className="px-4 py-3 text-slate-700 font-medium">
                      {acc.cost_center_name || "—"}
                    </td>
                    <td className="px-4 py-3">
                      {editingAcc?.id === acc.id ? (
                        <select
                          value={editingAccRole}
                          onChange={(e) => setEditingAccRole(e.target.value)}
                          className="rounded border border-slate-300 p-1 text-xs bg-white text-slate-800"
                        >
                          <option value="employee">Colaborador</option>
                          <option value="admin">Administrador</option>
                        </select>
                      ) : (
                        <Badge variant={acc.role === "admin" ? "default" : "secondary"}>
                          {acc.role.toUpperCase()}
                        </Badge>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      {editingAcc?.id === acc.id ? (
                        <label className="flex items-center gap-1.5 text-xs text-slate-700 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={editingAccEligible}
                            onChange={(e) => setEditingAccEligible(e.target.checked)}
                            className="rounded border-slate-300"
                          />
                          <span>Elegível</span>
                        </label>
                      ) : (
                        <span
                          className={`inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full ${
                            acc.is_eligible_for_booking
                              ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                              : "bg-amber-50 text-amber-800 border border-amber-200"
                          }`}
                        >
                          {acc.is_eligible_for_booking ? "Elegível" : "Bloqueado"}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right">
                      {editingAcc?.id === acc.id ? (
                        <div className="flex justify-end gap-1">
                          <Button size="sm" onClick={handleSaveAccount}>
                            Salvar
                          </Button>
                          <Button size="sm" variant="ghost" onClick={() => setEditingAcc(null)}>
                            Cancelar
                          </Button>
                        </div>
                      ) : (
                        <div className="flex items-center justify-end gap-1">
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => {
                              setEditingAcc(acc);
                              setEditingAccRole(acc.role);
                              setEditingAccEligible(acc.is_eligible_for_booking);
                            }}
                            className="text-xs font-medium text-slate-600 hover:text-slate-900 h-8 px-2"
                          >
                            <UserCheck className="h-4 w-4 mr-1 text-slate-500" />
                            Editar
                          </Button>
                          {acc.id !== user?.id && (
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => setAccountToDelete(acc)}
                              className="text-red-600 hover:text-red-700 hover:bg-red-50 h-8 w-8 p-0"
                              title="Excluir colaborador"
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          )}
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === "holidays" && (
        <div className="mt-6 space-y-4">
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs">
            <h3 className="text-sm font-bold text-slate-900 mb-1">Bloquear Novo Feriado</h3>
            <p className="text-xs text-slate-600 mb-3">
              Cadastrar feriado remove automaticamente todas as janelas de disponibilidade da data e impede reservas.
            </p>
            <div className="flex flex-wrap items-center gap-3">
              <input
                type="date"
                value={newHolidayDay}
                onChange={(e) => setNewHolidayDay(e.target.value)}
                className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-900 shadow-xs focus:ring-1 focus:ring-blue-500"
              />
              <Input
                type="text"
                placeholder="Descrição (ex: Tiradentes)"
                value={newHolidayDesc}
                onChange={(e) => setNewHolidayDesc(e.target.value)}
                className="max-w-xs text-sm"
              />
              <Button
                size="sm"
                onClick={handleCreateHoliday}
                disabled={createHolidayMutation.isPending}
                className="gap-1.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs"
              >
                <Plus className="h-4 w-4" />
                Bloquear Data
              </Button>
            </div>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs">
            <h3 className="text-sm font-bold text-slate-900 mb-3">Feriados Bloqueados</h3>
            <div className="divide-y divide-slate-100">
              {holidays?.items?.map((h) => (
                <div key={h.day} className="py-2.5 flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <Calendar className="h-4 w-4 text-slate-400" />
                    <span className="font-mono font-bold text-slate-900 mr-2">{h.day}</span>
                    <span className="text-slate-600 font-medium">{h.description}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline">Bloqueado</Badge>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => handleDeleteHoliday(h.day)}
                      className="text-red-600 hover:text-red-700 hover:bg-red-50 h-8 w-8 p-0"
                      title="Remover feriado"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
              {holidays?.items?.length === 0 && (
                <p className="text-xs text-slate-400 py-3">Nenhum feriado cadastrado.</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Modal: Criar Nova Conta de Colaborador */}
      <Dialog open={isCreatingAcc} onOpenChange={setIsCreatingAcc}>
        <DialogContent className="sm:max-w-md bg-white border border-slate-200 shadow-xl text-slate-900">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-lg font-bold text-slate-900">
              <UserPlus className="h-5 w-5 text-blue-600" />
              <span>Novo Colaborador</span>
            </DialogTitle>
            <DialogDescription className="text-sm font-medium text-slate-600">
              Cadastre um novo usuário no DeskFlow com vínculo a centro de custo.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-3.5 py-2">
            <div>
              <label className="text-xs font-bold text-slate-800 block mb-1">Nome Completo</label>
              <Input
                type="text"
                placeholder="Ex: Beatriz Lima"
                value={newAccName}
                onChange={(e) => setNewAccName(e.target.value)}
              />
            </div>

            <div>
              <label className="text-xs font-bold text-slate-800 block mb-1">E-mail Corporativo</label>
              <Input
                type="email"
                placeholder="ex: beatriz.lima@deskflow.com"
                value={newAccEmail}
                onChange={(e) => setNewAccEmail(e.target.value)}
              />
            </div>

            <div>
              <label className="text-xs font-bold text-slate-800 block mb-1">
                Senha Inicial (mínimo 12 caracteres)
              </label>
              <Input
                type="password"
                placeholder="Ex: SenhaForte123!"
                value={newAccPassword}
                onChange={(e) => setNewAccPassword(e.target.value)}
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-bold text-slate-800 block mb-1">Centro de Custo</label>
                <select
                  value={newAccCostCenterId}
                  onChange={(e) => setNewAccCostCenterId(e.target.value)}
                  className="w-full rounded-md border border-slate-300 bg-white p-2 text-xs font-medium text-slate-900 shadow-xs"
                >
                  <option value="">Selecione...</option>
                  {costCenters?.items?.map((cc) => (
                    <option key={cc.id} value={cc.id}>
                      {cc.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-xs font-bold text-slate-800 block mb-1">Perfil de Acesso</label>
                <select
                  value={newAccRole}
                  onChange={(e) => setNewAccRole(e.target.value as "employee" | "admin")}
                  className="w-full rounded-md border border-slate-300 bg-white p-2 text-xs font-medium text-slate-900 shadow-xs"
                >
                  <option value="employee">Colaborador</option>
                  <option value="admin">Administrador</option>
                </select>
              </div>
            </div>

            <div className="rounded-lg bg-slate-50 p-3 border border-slate-200">
              <label className="flex items-center gap-2 cursor-pointer text-xs font-semibold text-slate-800">
                <input
                  type="checkbox"
                  checked={newAccEligible}
                  onChange={(e) => setNewAccEligible(e.target.checked)}
                  className="rounded border-slate-300 h-4 w-4 text-blue-600"
                />
                <span>Habilitar elegibilidade para reserva imediata</span>
              </label>
              <p className="text-[11px] text-slate-500 mt-1 pl-6">
                Se desmarcado, o colaborador precisará atingir a frequência de 3 dias via integração de ponto antes de poder reservar.
              </p>
            </div>
          </div>

          <DialogFooter className="gap-2 sm:gap-0 border-t border-slate-100 pt-3">
            <Button variant="outline" onClick={() => setIsCreatingAcc(false)}>
              Cancelar
            </Button>
            <Button
              onClick={handleCreateAccount}
              disabled={createAccountMutation.isPending}
              className="bg-blue-600 hover:bg-blue-700 text-white font-semibold"
            >
              {createAccountMutation.isPending ? "Cadastrando..." : "Cadastrar Colaborador"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Modal: Criar Centro de Custo */}
      <Dialog open={isCreatingCc} onOpenChange={setIsCreatingCc}>
        <DialogContent className="sm:max-w-md bg-white border border-slate-200 shadow-xl text-slate-900">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-lg font-bold text-slate-900">
              <PieChart className="h-5 w-5 text-blue-600" />
              <span>Novo Centro de Custo</span>
            </DialogTitle>
            <DialogDescription className="text-sm font-medium text-slate-600">
              Defina o departamento e a cota mensal de horas para rateio corporativo.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-3 py-2">
            <div>
              <label className="text-xs font-bold text-slate-800 block mb-1">Nome do Departamento</label>
              <Input
                type="text"
                placeholder="Ex: Marketing Digital"
                value={newCcName}
                onChange={(e) => setNewCcName(e.target.value)}
              />
            </div>
            <div>
              <label className="text-xs font-bold text-slate-800 block mb-1">Cota Mensal (horas)</label>
              <Input
                type="number"
                value={newCcHours}
                onChange={(e) => setNewCcHours(Number(e.target.value))}
              />
            </div>
          </div>

          <DialogFooter className="gap-2 sm:gap-0 border-t border-slate-100 pt-3">
            <Button variant="outline" onClick={() => setIsCreatingCc(false)}>
              Cancelar
            </Button>
            <Button
              onClick={handleCreateCc}
              disabled={createCostCenterMutation.isPending}
              className="bg-blue-600 hover:bg-blue-700 text-white font-semibold"
            >
              {createCostCenterMutation.isPending ? "Salvando..." : "Salvar Centro de Custo"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Modal: Confirmar Exclusão de Colaborador */}
      <Dialog open={!!accountToDelete} onOpenChange={(open) => !open && setAccountToDelete(null)}>
        <DialogContent className="sm:max-w-md bg-white border border-slate-200 shadow-xl text-slate-900">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-lg font-bold text-red-600">
              <Trash2 className="h-5 w-5" />
              <span>Excluir Colaborador</span>
            </DialogTitle>
            <DialogDescription className="text-sm font-medium text-slate-600 pt-2 space-y-2">
              <p>
                Tem certeza que deseja excluir o colaborador{" "}
                <strong className="text-slate-900">{accountToDelete?.name}</strong> (
                {accountToDelete?.email})?
              </p>
              <p className="text-xs bg-red-50 text-red-800 p-2.5 rounded-lg border border-red-200">
                Esta ação revogará imediatamente o acesso do colaborador e cancelará quaisquer reservas e inscrições ativas em fila de espera.
              </p>
            </DialogDescription>
          </DialogHeader>

          <DialogFooter className="gap-2 sm:gap-0 border-t border-slate-100 pt-3">
            <Button
              variant="outline"
              onClick={() => setAccountToDelete(null)}
              disabled={deleteAccountMutation.isPending}
            >
              Cancelar
            </Button>
            <Button
              onClick={handleDeleteAccount}
              disabled={deleteAccountMutation.isPending}
              className="bg-red-600 hover:bg-red-700 text-white font-semibold"
            >
              {deleteAccountMutation.isPending ? "Excluindo..." : "Confirmar Exclusão"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Modal: Criar Novo Espaço */}
      <Dialog open={isCreatingWs} onOpenChange={setIsCreatingWs}>
        <DialogContent className="sm:max-w-md bg-white border border-slate-200 shadow-xl text-slate-900">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-lg font-bold text-slate-900">
              <Building2 className="h-5 w-5 text-blue-600" />
              <span>Novo Espaço / Estação</span>
            </DialogTitle>
            <DialogDescription className="text-sm font-medium text-slate-600">
              Cadastre uma nova estação individual ou sala de reunião com seus recursos.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-3.5 py-2">
            <div>
              <label className="text-xs font-bold text-slate-800 block mb-1">
                Código Identificador (ex: EST-105 ou SALA-201)
              </label>
              <Input
                type="text"
                placeholder="Ex: EST-105"
                value={newWsCode}
                onChange={(e) => setNewWsCode(e.target.value.toUpperCase())}
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-bold text-slate-800 block mb-1">Tipo</label>
                <select
                  value={newWsType}
                  onChange={(e) => {
                    const nextType = e.target.value as "estacao" | "sala";
                    setNewWsType(nextType);
                    if (nextType === "estacao") setNewWsCapacity(1);
                  }}
                  className="w-full rounded-md border border-slate-300 bg-white p-2 text-xs font-medium text-slate-900 shadow-xs"
                >
                  <option value="estacao">Estação Individual</option>
                  <option value="sala">Sala de Reunião</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-bold text-slate-800 block mb-1">Capacidade</label>
                <Input
                  type="number"
                  min={1}
                  disabled={newWsType === "estacao"}
                  value={newWsType === "estacao" ? 1 : newWsCapacity}
                  onChange={(e) => setNewWsCapacity(Number(e.target.value))}
                  className="text-sm"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-bold text-slate-800 block mb-1">Andar / Piso</label>
                <Input
                  type="text"
                  placeholder="Ex: 1º Andar"
                  value={newWsFloor}
                  onChange={(e) => setNewWsFloor(e.target.value)}
                />
              </div>

              <div>
                <label className="text-xs font-bold text-slate-800 block mb-1">Zona / Setor</label>
                <Input
                  type="text"
                  placeholder="Ex: Ala Norte"
                  value={newWsZone}
                  onChange={(e) => setNewWsZone(e.target.value)}
                />
              </div>
            </div>

            <div>
              <label className="text-xs font-bold text-slate-800 block mb-1.5">
                Recursos e Equipamentos Disponíveis
              </label>
              <div className="grid grid-cols-2 gap-2 bg-slate-50 p-3 rounded-lg border border-slate-200">
                {AVAILABLE_RESOURCES.map((res) => {
                  const checked = newWsResources.includes(res.id);
                  return (
                    <label
                      key={res.id}
                      className="flex items-center gap-2 cursor-pointer text-xs font-medium text-slate-700"
                    >
                      <input
                        type="checkbox"
                        checked={checked}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setNewWsResources([...newWsResources, res.id]);
                          } else {
                            setNewWsResources(newWsResources.filter((r) => r !== res.id));
                          }
                        }}
                        className="rounded border-slate-300 h-3.5 w-3.5 text-blue-600"
                      />
                      <span>{res.label}</span>
                    </label>
                  );
                })}
              </div>
            </div>
          </div>

          <DialogFooter className="gap-2 sm:gap-0 border-t border-slate-100 pt-3">
            <Button variant="outline" onClick={() => setIsCreatingWs(false)}>
              Cancelar
            </Button>
            <Button
              onClick={handleCreateWorkspace}
              disabled={createWorkspaceMutation.isPending}
              className="bg-blue-600 hover:bg-blue-700 text-white font-semibold"
            >
              {createWorkspaceMutation.isPending ? "Cadastrando..." : "Cadastrar Espaço"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Modal: Editar Espaço */}
      <Dialog open={!!editingWs} onOpenChange={(open) => !open && setEditingWs(null)}>
        <DialogContent className="sm:max-w-md bg-white border border-slate-200 shadow-xl text-slate-900">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-lg font-bold text-slate-900">
              <Building2 className="h-5 w-5 text-blue-600" />
              <span>Editar Espaço ({editingWs?.code})</span>
            </DialogTitle>
            <DialogDescription className="text-sm font-medium text-slate-600">
              Atualize informações de identificação, capacidade e recursos do espaço.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-3.5 py-2">
            <div>
              <label className="text-xs font-bold text-slate-800 block mb-1">
                Código Identificador
              </label>
              <Input
                type="text"
                value={editWsCode}
                onChange={(e) => setEditWsCode(e.target.value.toUpperCase())}
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-bold text-slate-800 block mb-1">Tipo</label>
                <select
                  value={editWsType}
                  onChange={(e) => {
                    const nextType = e.target.value as "estacao" | "sala";
                    setEditWsType(nextType);
                    if (nextType === "estacao") setEditWsCapacity(1);
                  }}
                  className="w-full rounded-md border border-slate-300 bg-white p-2 text-xs font-medium text-slate-900 shadow-xs"
                >
                  <option value="estacao">Estação Individual</option>
                  <option value="sala">Sala de Reunião</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-bold text-slate-800 block mb-1">Capacidade</label>
                <Input
                  type="number"
                  min={1}
                  disabled={editWsType === "estacao"}
                  value={editWsType === "estacao" ? 1 : editWsCapacity}
                  onChange={(e) => setEditWsCapacity(Number(e.target.value))}
                  className="text-sm"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-bold text-slate-800 block mb-1">Andar / Piso</label>
                <Input
                  type="text"
                  value={editWsFloor}
                  onChange={(e) => setEditWsFloor(e.target.value)}
                />
              </div>

              <div>
                <label className="text-xs font-bold text-slate-800 block mb-1">Zona / Setor</label>
                <Input
                  type="text"
                  value={editWsZone}
                  onChange={(e) => setEditWsZone(e.target.value)}
                />
              </div>
            </div>

            <div>
              <label className="text-xs font-bold text-slate-800 block mb-1.5">
                Recursos e Equipamentos Disponíveis
              </label>
              <div className="grid grid-cols-2 gap-2 bg-slate-50 p-3 rounded-lg border border-slate-200">
                {AVAILABLE_RESOURCES.map((res) => {
                  const checked = editWsResources.includes(res.id);
                  return (
                    <label
                      key={res.id}
                      className="flex items-center gap-2 cursor-pointer text-xs font-medium text-slate-700"
                    >
                      <input
                        type="checkbox"
                        checked={checked}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setEditWsResources([...editWsResources, res.id]);
                          } else {
                            setEditWsResources(editWsResources.filter((r) => r !== res.id));
                          }
                        }}
                        className="rounded border-slate-300 h-3.5 w-3.5 text-blue-600"
                      />
                      <span>{res.label}</span>
                    </label>
                  );
                })}
              </div>
            </div>
          </div>

          <DialogFooter className="gap-2 sm:gap-0 border-t border-slate-100 pt-3">
            <Button variant="outline" onClick={() => setEditingWs(null)}>
              Cancelar
            </Button>
            <Button
              onClick={handleSaveWorkspace}
              disabled={updateWorkspaceMutation.isPending}
              className="bg-blue-600 hover:bg-blue-700 text-white font-semibold"
            >
              {updateWorkspaceMutation.isPending ? "Salvando..." : "Salvar Alterações"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Modal: Confirmar Exclusão de Espaço */}
      <Dialog open={!!wsToDelete} onOpenChange={(open) => !open && setWsToDelete(null)}>
        <DialogContent className="sm:max-w-md bg-white border border-slate-200 shadow-xl text-slate-900">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-lg font-bold text-red-600">
              <Trash2 className="h-5 w-5" />
              <span>Excluir Espaço</span>
            </DialogTitle>
            <DialogDescription className="text-sm font-medium text-slate-600 pt-2 space-y-2">
              <p>
                Tem certeza que deseja excluir o espaço{" "}
                <strong className="text-slate-900">{wsToDelete?.code}</strong> ({wsToDelete?.floor} • {wsToDelete?.zone})?
              </p>
              <p className="text-xs bg-red-50 text-red-800 p-2.5 rounded-lg border border-red-200">
                Atenção: Espaços com reservas ativas ou agendadas não podem ser excluídos. Cancele as reservas antes se desejar desativar o espaço permanentemente.
              </p>
            </DialogDescription>
          </DialogHeader>

          <DialogFooter className="gap-2 sm:gap-0 border-t border-slate-100 pt-3">
            <Button
              variant="outline"
              onClick={() => setWsToDelete(null)}
              disabled={deleteWorkspaceMutation.isPending}
            >
              Cancelar
            </Button>
            <Button
              onClick={handleDeleteWorkspace}
              disabled={deleteWorkspaceMutation.isPending}
              className="bg-red-600 hover:bg-red-700 text-white font-semibold"
            >
              {deleteWorkspaceMutation.isPending ? "Excluindo..." : "Confirmar Exclusão"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
