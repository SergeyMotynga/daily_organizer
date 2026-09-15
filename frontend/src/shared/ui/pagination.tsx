import { ChevronLeft, ChevronRight } from "lucide-react";
import { SelectCombobox } from "./select-combobox";

type PaginationProps = {
  className: string;
  total: number;
  label: string;
  limit: number;
  offset: number;
  onLimitChange: (limit: number) => void;
  onOffsetChange: (offset: number) => void;
};

export function Pagination({ className, total, label, limit, offset, onLimitChange, onOffsetChange }: PaginationProps) {
  const pageCount = Math.max(1, Math.ceil(total / limit));
  const page = Math.min(pageCount, Math.floor(offset / limit) + 1);
  const firstPage = Math.max(1, Math.min(page - 1, pageCount - 2));
  const pages = Array.from({ length: Math.min(3, pageCount) }, (_, index) => firstPage + index);
  return (
    <footer className={className}>
      <span>{label}: {total}</span>
      <div>
        <SelectCombobox label="Задач на странице" value={String(limit)} options={[10, 20, 50].map((item) => ({ value: String(item), label: `${item} на странице` }))} onChange={(value) => onLimitChange(Number(value))} />
        <button type="button" aria-label="Предыдущая страница" disabled={page === 1} onClick={() => onOffsetChange(Math.max(0, offset - limit))}><ChevronLeft size={17} /></button>
        {pages.map((value) => <button key={value} type="button" aria-label={`Страница ${value}`} aria-current={value === page ? "page" : undefined} className={value === page ? `${className}__page` : undefined} onClick={() => onOffsetChange((value - 1) * limit)}>{value}</button>)}
        <button type="button" aria-label="Следующая страница" disabled={page >= pageCount} onClick={() => onOffsetChange(offset + limit)}><ChevronRight size={17} /></button>
      </div>
    </footer>
  );
}
