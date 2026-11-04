"use client";

import { useState } from "react";
import {
  AlertTriangle,
  Building,
  CheckCircle2,
  Lock,
  PieChart,
  Shield,
  UserCheck,
  Users,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  AccountApiItem,
  CostCenterApiItem,
  useAdminAccounts,
  useAdminCostCenters,
  useAdminHolidays,
  useAdminQuotas,
  useUpdateAccount,
  useUpdateCostCenter,
} from "@/features/admin/hooks/use-admin";
import { useCurrentUser } from "@/features/auth/hooks/use-auth";

export default function AdminPage() {
  const { data: user, isLoading: userLoading } = useCurrentUser();
  const [activeTab, setActiveTab] = useState<"quotas" | "accounts" | "holidays">("quotas");

  const { data: costCenters } = useAdminCostCenters();
  const { data: quotas } = useAdminQuotas();
  const updateCostCenterMutation = useUpdateCostCenter();

  const { data: accounts } = useAdminAccounts();
  const updateAccountMutation = useUpdateAccount();

  const { data: holidays } = useAdminHolidays();

  const [editingCc, setEditingCc] = useState<CostCenterApiItem | null>(null);
  const [editingCcHours, setEditingCcHours] = useState<number>(0);

  const [editingAcc, setEditingAcc] = useState<AccountApiItem | null>(null);
  const [editingAccRole, setEditingAccRole] = useState<string>("employee");
  const [editingAccEligible, setEditingAccEligible] = useState<boolean>(true);

  const [feedback, setFeedback] = useState<{ type: "success" | "error"; text: string } | null>(null);

  if (userLoading) {
    return (
      <div className="mx-auto max-w-7xl p-8">
        <div className="h-10 w-48 animate-pulse rounded bg-slate-200" />
      </div>
    );
  }

  if (!user?.isAdmin()) {
    return (
      <div className="mx-auto max-w-md py-20 text-center">
        <Lock className="mx-auto h-12 w-12 text-slate-400" />
        <h2 className="mt-3 text-lg font-bold text-slate-900">Acesso Restrito</h2>
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

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="border-b border-slate-200 pb-5">
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
          <Shield className="h-6 w-6 text-blue-600" />
          Painel de Administração
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Configuração de cotas por centro de custo (UC11), gestão de contas (UC17) e controle de feriados.
        </p>
      </div>

      {feedback && (
        <div
          className={`mt-4 rounded-md p-3 text-sm border flex items-center gap-2 ${
            feedback.type === "success"
              ? "bg-emerald-50 text-emerald-800 border-emerald-200"
              : "bg-red-50 text-red-700 border-red-200"
          }`}
        >
          {feedback.type === "success" ? (
            <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600" />
          ) : (
            <AlertTriangle className="h-4 w-4 shrink-0 text-red-600" />
          )}
          <span>{feedback.text}</span>
        </div>
      )}

      <div className="mt-6 flex border-b border-slate-200 space-x-4">
        <button
          onClick={() => setActiveTab("quotas")}
          className={`pb-3 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${
            activeTab === "quotas"
              ? "border-blue-600 text-blue-600"
              : "border-transparent text-slate-500 hover:text-slate-700"
          }`}
        >
          <PieChart className="h-4 w-4" />
          Cotas & Centros de Custo
        </button>

        <button
          onClick={() => setActiveTab("accounts")}
          className={`pb-3 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${
            activeTab === "accounts"
              ? "border-blue-600 text-blue-600"
              : "border-transparent text-slate-500 hover:text-slate-700"
          }`}
        >
          <Users className="h-4 w-4" />
          Contas & Elegibilidade
        </button>

        <button
          onClick={() => setActiveTab("holidays")}
          className={`pb-3 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${
            activeTab === "holidays"
              ? "border-blue-600 text-blue-600"
              : "border-transparent text-slate-500 hover:text-slate-700"
          }`}
        >
          <Building className="h-4 w-4" />
          Feriados & Bloqueios
        </button>
      </div>

      {activeTab === "quotas" && (
        <div className="mt-6 space-y-4">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {costCenters?.items?.map((cc) => {
              const q = quotas?.items?.find((q) => q.cost_center_id === cc.id);
              const usedHours = q?.used_hours ?? 0;
              const totalHours = cc.monthly_quota_hours;
              const percent = totalHours > 0 ? (usedHours / totalHours) * 100 : 0;
              const isAlert95 = percent >= 95;
              const isAlert80 = percent >= 80 && percent < 95;

              return (
                <Card key={cc.id} className="shadow-xs">
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-base font-bold text-slate-900">
                        {cc.name}
                      </CardTitle>
                      {isAlert95 && <Badge variant="destructive">Alerta 95%</Badge>}
                      {isAlert80 && <Badge variant="warning">Alerta 80%</Badge>}
                      {!isAlert80 && !isAlert95 && <Badge variant="secondary">Normal</Badge>}
                    </div>
                    <CardDescription className="text-xs">
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

      {activeTab === "accounts" && (
        <div className="mt-6">
          <div className="rounded-xl border border-slate-200 bg-white overflow-hidden shadow-xs">
            <table className="w-full text-left text-sm text-slate-600">
              <thead className="bg-slate-50 text-xs font-semibold uppercase text-slate-500 border-b border-slate-200">
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
                  <tr key={acc.id} className="hover:bg-slate-50/50">
                    <td className="px-4 py-3">
                      <div className="font-medium text-slate-900">{acc.name}</div>
                      <div className="text-xs text-slate-400">{acc.email}</div>
                    </td>
                    <td className="px-4 py-3 text-xs">
                      {acc.cost_center_name || "Não atribuído"}
                    </td>
                    <td className="px-4 py-3">
                      {editingAcc?.id === acc.id ? (
                        <select
                          value={editingAccRole}
                          onChange={(e) => setEditingAccRole(e.target.value)}
                          className="rounded border border-slate-300 p-1 text-xs"
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
                        <label className="flex items-center gap-1.5 text-xs">
                          <input
                            type="checkbox"
                            checked={editingAccEligible}
                            onChange={(e) => setEditingAccEligible(e.target.checked)}
                          />
                          <span>Elegível</span>
                        </label>
                      ) : (
                        <Badge variant={acc.is_eligible_for_booking ? "success" : "outline"}>
                          {acc.is_eligible_for_booking ? "Elegível" : "Bloqueado"}
                        </Badge>
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
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => {
                            setEditingAcc(acc);
                            setEditingAccRole(acc.role);
                            setEditingAccEligible(acc.is_eligible_for_booking);
                          }}
                        >
                          <UserCheck className="h-4 w-4 mr-1" />
                          Editar
                        </Button>
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
        <div className="mt-6 space-y-3">
          <div className="rounded-xl border border-slate-200 bg-white p-4">
            <h3 className="text-sm font-semibold text-slate-900 mb-2">Feriados Bloqueados</h3>
            <div className="divide-y divide-slate-100">
              {holidays?.items?.map((h) => (
                <div key={h.day} className="py-2 flex items-center justify-between text-sm">
                  <div>
                    <span className="font-mono font-semibold text-slate-800 mr-2">{h.day}</span>
                    <span className="text-slate-600">{h.description}</span>
                  </div>
                  <Badge variant="outline">Bloqueado</Badge>
                </div>
              ))}
              {holidays?.items?.length === 0 && (
                <p className="text-xs text-slate-400 py-2">Nenhum feriado cadastrado.</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

