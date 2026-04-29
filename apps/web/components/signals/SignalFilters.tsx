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
    <aside className={styles.filters} aria-label="Signal filters">
      <div>
        <p className={styles.eyebrow}>Filters</p>
        <h2 className={styles.panelTitle}>Review Queue</h2>
      </div>

      <label className={styles.field}>
        <span className={styles.fieldLabel}>Platform</span>
        <input
          className={styles.input}
          disabled={isDisabled}
          onChange={(event) => updateFilter("platform", event.target.value)}
          placeholder="Any platform"
          value={filters.platform}
        />
      </label>

      <label className={styles.field}>
        <span className={styles.fieldLabel}>Signal type</span>
        <input
          className={styles.input}
          disabled={isDisabled}
          onChange={(event) => updateFilter("signalType", event.target.value)}
          placeholder="Any type"
          value={filters.signalType}
        />
      </label>

      <label className={styles.field}>
        <span className={styles.fieldLabel}>Status</span>
        <select
          className={styles.input}
          disabled={isDisabled}
          onChange={(event) => updateFilter("status", event.target.value)}
          value={filters.status}
        >
          <option value="">Any status</option>
          <option value="new">new</option>
          <option value="saved">saved</option>
          <option value="ignored">ignored</option>
          <option value="reviewed">reviewed</option>
        </select>
      </label>

      <label className={styles.field}>
        <span className={styles.fieldLabel}>Keyword</span>
        <input
          className={styles.input}
          disabled={isDisabled}
          onChange={(event) => updateFilter("keyword", event.target.value)}
          placeholder="Search summary or hit"
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
          <strong>High Value only</strong>
          <small>min_pain_level=70 plus confidence 60+</small>
        </span>
      </label>

      <label className={styles.field}>
        <span className={styles.fieldLabel}>Minimum pain level</span>
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
          <span className={styles.fieldLabel}>Date from</span>
          <input
            className={styles.input}
            disabled={isDisabled}
            onChange={(event) => updateFilter("dateFrom", event.target.value)}
            type="date"
            value={filters.dateFrom}
          />
        </label>
        <label className={styles.field}>
          <span className={styles.fieldLabel}>Date to</span>
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
        Reset Filters
      </Button>
    </aside>
  );
}
