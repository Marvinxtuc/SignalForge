"use client";

import { Button } from "../ui/Button";
import styles from "./SignalInbox.module.css";

export type SignalFilterValues = {
  platform: string;
  signalType: string;
  status: string;
  keyword: string;
  minPainLevel: string;
  dateFrom: string;
  dateTo: string;
  highValueOnly: boolean;
};

type SignalFiltersProps = {
  filters: SignalFilterValues;
  isDisabled: boolean;
  onChange: (filters: SignalFilterValues) => void;
};

const EMPTY_FILTERS: SignalFilterValues = {
  platform: "",
  signalType: "",
  status: "",
  keyword: "",
  minPainLevel: "",
  dateFrom: "",
  dateTo: "",
  highValueOnly: false
};

export function SignalFilters({ filters, isDisabled, onChange }: SignalFiltersProps) {
  function updateFilter<Key extends keyof SignalFilterValues>(
    key: Key,
    value: SignalFilterValues[Key]
  ) {
    onChange({ ...filters, [key]: value });
  }

  return (
    <aside className={styles.filters} aria-label="信号筛选器">
      <div>
        <p className={styles.eyebrow}>筛选器</p>
        <h2 className={styles.panelTitle}>待审信号</h2>
      </div>

      <label className={styles.field}>
        <span className={styles.fieldLabel}>平台</span>
        <select
          className={styles.input}
          disabled={isDisabled}
          onChange={(event) => updateFilter("platform", event.target.value)}
          value={filters.platform}
        >
          <option value="">全部平台</option>
          <option value="reddit">Reddit</option>
          <option value="product_hunt">Product Hunt</option>
          <option value="x">X</option>
          <option value="discord">Discord</option>
        </select>
      </label>

      <label className={styles.field}>
        <span className={styles.fieldLabel}>信号类型</span>
        <input
          className={styles.input}
          disabled={isDisabled}
          onChange={(event) => updateFilter("signalType", event.target.value)}
          placeholder="全部类型"
          value={filters.signalType}
        />
      </label>

      <label className={styles.field}>
        <span className={styles.fieldLabel}>状态</span>
        <select
          className={styles.input}
          disabled={isDisabled}
          onChange={(event) => updateFilter("status", event.target.value)}
          value={filters.status}
        >
          <option value="">全部状态</option>
          <option value="new">新建</option>
          <option value="saved">已保存</option>
          <option value="ignored">已忽略</option>
          <option value="reviewed">已复核</option>
        </select>
      </label>

      <label className={styles.field}>
        <span className={styles.fieldLabel}>关键词</span>
        <input
          className={styles.input}
          disabled={isDisabled}
          onChange={(event) => updateFilter("keyword", event.target.value)}
          placeholder="搜索摘要或关键词"
          value={filters.keyword}
        />
      </label>

      <label className={styles.checkboxField}>
        <input
          checked={filters.highValueOnly}
          disabled={isDisabled}
          onChange={(event) => updateFilter("highValueOnly", event.target.checked)}
          type="checkbox"
        />
        <span>
          <strong>仅看高价值</strong>
          <small>痛点分不低于 70，信号置信度不低于 60</small>
        </span>
      </label>

      <label className={styles.field}>
        <span className={styles.fieldLabel}>最低痛点分</span>
        <input
          className={styles.input}
          disabled={isDisabled || filters.highValueOnly}
          min="0"
          max="100"
          onChange={(event) => updateFilter("minPainLevel", event.target.value)}
          placeholder={filters.highValueOnly ? "70" : "0-100"}
          type="number"
          value={filters.highValueOnly ? "70" : filters.minPainLevel}
        />
      </label>

      <div className={styles.dateGrid}>
        <label className={styles.field}>
          <span className={styles.fieldLabel}>开始日期</span>
          <input
            className={styles.input}
            disabled={isDisabled}
            onChange={(event) => updateFilter("dateFrom", event.target.value)}
            type="date"
            value={filters.dateFrom}
          />
        </label>
        <label className={styles.field}>
          <span className={styles.fieldLabel}>结束日期</span>
          <input
            className={styles.input}
            disabled={isDisabled}
            onChange={(event) => updateFilter("dateTo", event.target.value)}
            type="date"
            value={filters.dateTo}
          />
        </label>
      </div>

      <Button disabled={isDisabled} onClick={() => onChange(EMPTY_FILTERS)} size="small">
        重置筛选
      </Button>
    </aside>
  );
}
