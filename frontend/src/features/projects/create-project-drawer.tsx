import { useEffect, useRef, useState, type FormEvent } from "react";
import { ArrowDown, ArrowUp, Plus, Trash2, X } from "lucide-react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createProject, createProjectColumn, deleteProjectColumn, getProject, reorderProjectColumns, updateProject, updateProjectColumn } from "./api";
import { projectQueryKeys } from "./queries";
import { Checkbox } from "../../shared/ui/checkbox";
import { isComboboxHandlingEscape, useTaskDrawerTransition } from "../tasks/task-drawer-transition";

const defaultColumns = ["Бэклог", "К выполнению", "В работе", "На проверке", "Готово"];
type DraftStage = { key: string; title: string };

export function CreateProjectDrawer({ onClose: onDismiss }: { onClose: () => void }) {
  const { onClose, isClosing } = useTaskDrawerTransition(onDismiss);
  const queryClient = useQueryClient();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [stages, setStages] = useState<DraftStage[]>(defaultColumns.map((name,index) => ({key:String(index),title:name})));
  const [completion, setCompletion] = useState("4");
  const [newStage, setNewStage] = useState("");
  const [error, setError] = useState<string | null>(null);
  const createdProjectId = useRef<string | null>(null);
  const stageIds = useRef(new Map<string,string>());
  const mutation = useMutation({
    mutationFn: async () => {
      if (!createdProjectId.current) {
        const project = await createProject({ title: title.trim(), description: description.trim() || null });
        createdProjectId.current = project.id;
        [...project.columns].sort((a,b) => a.position - b.position).forEach((column,index) => stageIds.current.set(String(index),column.id));
      } else await updateProject(createdProjectId.current, { title: title.trim(), description: description.trim() || null });
      const projectId = createdProjectId.current;
      for (const stage of stages) {
        const columnId = stageIds.current.get(stage.key);
        if (columnId) await updateProjectColumn(projectId,columnId,{title:stage.title.trim()});
        else {
          const column = await createProjectColumn(projectId,stage.title.trim());
          stageIds.current.set(stage.key,column.id);
        }
      }
      const completionId = stageIds.current.get(completion)!;
      await updateProjectColumn(projectId,completionId,{is_completion_column:true});
      const wantedIds = stages.map((stage) => stageIds.current.get(stage.key)!);
      // Получаем фактический список, чтобы повторный запуск продолжал сохранённый проект.
      const current = await getProject(projectId);
      for (const column of current.columns) if (!wantedIds.includes(column.id)) await deleteProjectColumn(projectId,column.id);
      await reorderProjectColumns(projectId,wantedIds);
    },
    onSettled: async () => { await queryClient.invalidateQueries({queryKey:projectQueryKeys.all}); }
  });

  useEffect(() => {
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    function handleKeyDown(event: KeyboardEvent) {
      if (isComboboxHandlingEscape(event)) return;
      if (event.key === "Escape" && !mutation.isPending) onClose();
    }
    document.addEventListener("keydown", handleKeyDown, true);
    return () => { document.body.style.overflow = previousOverflow; document.removeEventListener("keydown", handleKeyDown, true); };
  }, [mutation.isPending,onClose]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!title.trim()) { setError("Введите название проекта."); return; }
    if (!stages.length || stages.some((stage) => !stage.title.trim())) { setError("Укажите название каждого этапа."); return; }
    if (!stages.some((stage) => stage.key === completion)) { setError("Выберите завершающий этап."); return; }
    setError(null);
    try { await mutation.mutateAsync(); onClose(); }
    catch { setError(createdProjectId.current ? "Проект создан, но этапы сохранены не полностью. Повторите сохранение — оно продолжится в этом проекте." : "Не удалось создать проект. Попробуйте ещё раз."); }
  }
  function move(index:number, direction:number) {
    const next = [...stages];
    [next[index],next[index+direction]] = [next[index+direction],next[index]];
    setStages(next);
  }
  return <div className={`task-drawer-layer${isClosing ? " task-drawer-layer--closing" : ""}`}>
    <button className="task-drawer-backdrop" type="button" aria-label="Закрыть" onClick={onClose} disabled={mutation.isPending} />
    <aside className="task-drawer route-project-create" role="dialog" aria-modal="true" aria-labelledby="new-project-title" inert={isClosing}>
      <header className="task-drawer__header"><h2 id="new-project-title">Новый проект</h2><button className="task-drawer__close" type="button" onClick={onClose} disabled={mutation.isPending} aria-label="Закрыть"><X size={25} /></button></header>
      <form className="task-create-form" onSubmit={submit} noValidate>
        <div className="task-create-form__body"><fieldset className="route-project-create__fields" disabled={mutation.isPending}>
          <label className="task-create-field"><span>Название <b>*</b></span><input autoFocus maxLength={255} value={title} onChange={(event) => {setTitle(event.target.value);setError(null);}} placeholder="Название проекта" /></label>
          <label className="task-create-field"><span>Описание · необязательно</span><textarea rows={3} value={description} onChange={(event) => setDescription(event.target.value)} placeholder="Коротко о цели проекта" /></label>
          <div className="route-stages-heading"><h3>Этапы проекта</h3><span>Один этап должен завершать задачи</span></div>
          <div className="route-stage-drafts">{stages.map((stage,index) => <div className="route-stage-draft" key={stage.key}>
            <div className="route-stage-order"><button type="button" disabled={index===0} aria-label={`Переместить этап ${index+1} выше`} onClick={() => move(index,-1)}><ArrowUp size={16} /></button><button type="button" disabled={index===stages.length-1} aria-label={`Переместить этап ${index+1} ниже`} onClick={() => move(index,1)}><ArrowDown size={16} /></button></div>
            <input aria-label={`Название этапа ${index+1}`} value={stage.title} maxLength={255} onChange={(event) => setStages(stages.map((item) => item.key === stage.key ? {...item,title:event.target.value} : item))} />
            <Checkbox isSelected={completion===stage.key} onChange={() => setCompletion(stage.key)} aria-label={`Завершающий этап: ${stage.title}`}>Завершает задачи</Checkbox>
            <button type="button" disabled={completion===stage.key || stages.length===1} aria-label={`Удалить этап ${stage.title}`} onClick={() => setStages(stages.filter((item) => item.key!==stage.key))}><Trash2 size={19} /></button>
          </div>)}</div>
          <div className="route-stage-add"><input aria-label="Новый этап" placeholder="Название нового этапа" maxLength={255} value={newStage} onChange={(event) => setNewStage(event.target.value)} /><button type="button" disabled={!newStage.trim()} onClick={() => {setStages([...stages,{key:crypto.randomUUID(),title:newStage.trim()}]);setNewStage("");}}><Plus size={18} />Добавить этап</button></div>
          <p className="route-form-note">Этапы можно переименовать и переставить. Завершающий этап отмечает обычные задачи выполненными; повторяющиеся задачи в него не перемещаются.</p>
        </fieldset>{error ? <div className="task-create-error" role="alert">{error}</div> : null}</div>
        <footer className="task-create-form__footer"><button className="task-create-button" type="button" onClick={onClose} disabled={mutation.isPending}>Отмена</button><button className="task-create-button task-create-button--primary" type="submit" disabled={mutation.isPending}>{mutation.isPending ? "Сохраняем…" : createdProjectId.current ? "Продолжить сохранение" : "Создать проект"}</button></footer>
      </form>
    </aside>
  </div>;
}
