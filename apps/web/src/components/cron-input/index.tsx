import { useState, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Info } from 'lucide-react';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';

interface CronInputProps {
  value?: string;
  onChange?: (cronExpression: string) => void;
  className?: string;
}

interface CronFields {
  second: string;
  minute: string;
  hour: string;
  day: string;
  month: string;
  weekday: string;
}

const FIELD_LABELS = {
  second: 'Second',
  minute: 'Minute',
  hour: 'Hour',
  day: 'Day',
  month: 'Month',
  weekday: 'Weekday',
};

const FIELD_RANGES = {
  second: { min: 0, max: 59, help: '0-59' },
  minute: { min: 0, max: 59, help: '0-59' },
  hour: { min: 0, max: 23, help: '0-23' },
  day: { min: 1, max: 31, help: '1-31' },
  month: { min: 1, max: 12, help: '1-12' },
  weekday: { min: 0, max: 7, help: '0-7 (0 & 7 = Sunday)' },
};

const MONTH_NAMES = [
  'Jan',
  'Feb',
  'Mar',
  'Apr',
  'May',
  'Jun',
  'Jul',
  'Aug',
  'Sep',
  'Oct',
  'Nov',
  'Dec',
];

const WEEKDAY_NAMES = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

// Parse cron expression into fields
function parseCronExpression(cron: string): CronFields {
  const parts = cron.trim().split(/\s+/);

  // Handle both 5-field (minute hour day month weekday) and 6-field (second minute hour day month weekday)
  if (parts.length === 5) {
    return {
      second: '0',
      minute: parts[0],
      hour: parts[1],
      day: parts[2],
      month: parts[3],
      weekday: parts[4],
    };
  } else if (parts.length === 6) {
    return {
      second: parts[0],
      minute: parts[1],
      hour: parts[2],
      day: parts[3],
      month: parts[4],
      weekday: parts[5],
    };
  }

  return {
    second: '*',
    minute: '*',
    hour: '*',
    day: '*',
    month: '*',
    weekday: '*',
  };
}

// Build cron expression from fields
function buildCronExpression(fields: CronFields): string {
  return `${fields.second} ${fields.minute} ${fields.hour} ${fields.day} ${fields.month} ${fields.weekday}`;
}

// Validate field value
function validateField(
  value: string,
  min: number,
  max: number
): { isValid: boolean; error?: string } {
  if (!value || value.trim() === '') {
    return { isValid: false, error: 'Required' };
  }

  const trimmed = value.trim();

  // Allow wildcard
  if (trimmed === '*') {
    return { isValid: true };
  }

  // Allow step values like */5
  if (trimmed.startsWith('*/')) {
    const step = trimmed.substring(2);
    if (/^\d+$/.test(step)) {
      const stepNum = parseInt(step, 10);
      if (stepNum > 0 && stepNum <= max) {
        return { isValid: true };
      }
      return { isValid: false, error: `Step must be 1-${max}` };
    }
    return { isValid: false, error: 'Invalid step format' };
  }

  // Allow single number
  if (/^\d+$/.test(trimmed)) {
    const num = parseInt(trimmed, 10);
    if (num >= min && num <= max) {
      return { isValid: true };
    }
    return { isValid: false, error: `Must be ${min}-${max}` };
  }

  // Allow ranges like 1-5
  if (/^\d+-\d+$/.test(trimmed)) {
    const [start, end] = trimmed.split('-').map(Number);
    if (start >= min && end <= max && start <= end) {
      return { isValid: true };
    }
    return { isValid: false, error: `Range must be ${min}-${max}` };
  }

  // Allow lists like 1,3,5
  if (/^[\d,]+$/.test(trimmed)) {
    const numbers = trimmed.split(',').map(Number);
    const allValid = numbers.every((n) => n >= min && n <= max);
    if (allValid) {
      return { isValid: true };
    }
    return { isValid: false, error: `All values must be ${min}-${max}` };
  }

  // Allow range with step like 1-10/2
  if (/^\d+-\d+\/\d+$/.test(trimmed)) {
    const [range, step] = trimmed.split('/');
    const [start, end] = range.split('-').map(Number);
    const stepNum = parseInt(step, 10);
    if (start >= min && end <= max && start <= end && stepNum > 0) {
      return { isValid: true };
    }
    return { isValid: false, error: 'Invalid range/step format' };
  }

  return { isValid: false, error: 'Invalid format' };
}

export function CronInput({ value = '', onChange, className }: CronInputProps) {
  const [fields, setFields] = useState<CronFields>(() => parseCronExpression(value));
  const [fieldErrors, setFieldErrors] = useState<Partial<Record<keyof CronFields, string>>>({});

  // Update fields when value prop changes
  useEffect(() => {
    if (value) {
      const parsed = parseCronExpression(value);
      setFields(parsed);
    }
  }, [value]);

  const handleFieldChange = (fieldName: keyof CronFields, newValue: string) => {
    const updatedFields = { ...fields, [fieldName]: newValue };
    setFields(updatedFields);

    // Validate the field
    const range = FIELD_RANGES[fieldName];
    const validation = validateField(newValue, range.min, range.max);

    if (validation.isValid) {
      // Remove error for this field
      setFieldErrors((prev) => {
        const next = { ...prev };
        delete next[fieldName];
        return next;
      });

      // Build and emit cron expression
      const cronExpression = buildCronExpression(updatedFields);
      onChange?.(cronExpression);
    } else {
      // Set error for this field
      setFieldErrors((prev) => ({
        ...prev,
        [fieldName]: validation.error,
      }));
    }
  };

  const getFieldDisplayValue = (fieldName: keyof CronFields, fieldValue: string): string => {
    if (fieldName === 'month' && /^\d+$/.test(fieldValue)) {
      const monthNum = parseInt(fieldValue, 10);
      if (monthNum >= 1 && monthNum <= 12) {
        return `${fieldValue} (${MONTH_NAMES[monthNum - 1]})`;
      }
    }
    if (fieldName === 'weekday' && /^[0-7]$/.test(fieldValue)) {
      const dayNum = parseInt(fieldValue, 10);
      if (dayNum === 0 || dayNum === 7) {
        return `${fieldValue} (Sun)`;
      } else if (dayNum >= 1 && dayNum <= 6) {
        return `${fieldValue} (${WEEKDAY_NAMES[dayNum]})`;
      }
    }
    return fieldValue;
  };

  return (
    <TooltipProvider>
      <div className={cn('space-y-4', className)}>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {(['second', 'minute', 'hour', 'day', 'month', 'weekday'] as const).map((fieldName) => {
            const range = FIELD_RANGES[fieldName];
            const hasError = !!fieldErrors[fieldName];
            const displayValue = getFieldDisplayValue(fieldName, fields[fieldName]);

            return (
              <div key={fieldName} className="space-y-2">
                <div className="flex items-center gap-1.5">
                  <Label htmlFor={`cron-${fieldName}`} className="text-xs font-medium">
                    {FIELD_LABELS[fieldName]}
                  </Label>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Info className="h-3 w-3 text-muted-foreground cursor-help" />
                    </TooltipTrigger>
                    <TooltipContent>
                      <div className="text-xs space-y-1">
                        <p className="font-medium">Range: {range.help}</p>
                        <p>Use * for any value</p>
                        <p>Use */N for every N</p>
                        <p>Use 1-5 for range</p>
                        <p>Use 1,3,5 for list</p>
                      </div>
                    </TooltipContent>
                  </Tooltip>
                </div>
                <Input
                  id={`cron-${fieldName}`}
                  value={fields[fieldName]}
                  onChange={(e) => handleFieldChange(fieldName, e.target.value)}
                  placeholder="*"
                  className={cn(
                    'font-mono text-sm h-10',
                    hasError && 'border-destructive focus-visible:ring-destructive'
                  )}
                />
                {hasError && <p className="text-xs text-destructive">{fieldErrors[fieldName]}</p>}
              </div>
            );
          })}
        </div>
      </div>
    </TooltipProvider>
  );
}
