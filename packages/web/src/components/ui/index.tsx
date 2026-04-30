import {
  type CSSProperties,
  type FormEvent,
  type HTMLAttributes,
  type InputHTMLAttributes,
  type ReactElement,
  type ReactNode,
  cloneElement,
  createContext,
  isValidElement,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { Accordion, Dialog, RadioGroup as RadioPrimitive, Tooltip as TooltipPrimitive } from "radix-ui";
import { Cross1Icon } from "@radix-ui/react-icons";
import AppButton from "./Button";
import AppSelect, { type SelectOption } from "./Select";
import { EmptyState, Spinner, AppBadge } from "./Status";
import { TextArea, TextInput } from "./Field";
import { cx } from "./radix";

type FieldName = string | number | Array<string | number>;

const toPath = (name: FieldName) => (Array.isArray(name) ? name.map(String) : [String(name)]);

const getIn = (source: Record<string, unknown>, name: FieldName) =>
  toPath(name).reduce<unknown>((value, key) => {
    if (value && typeof value === "object") {
      return (value as Record<string, unknown>)[key];
    }
    return undefined;
  }, source);

const setIn = (source: Record<string, unknown>, name: FieldName, value: unknown) => {
  const next = { ...source };
  let cursor: Record<string, unknown> = next;
  const path = toPath(name);
  path.forEach((key, index) => {
    if (index === path.length - 1) {
      cursor[key] = value;
      return;
    }
    const child = cursor[key];
    cursor[key] = child && typeof child === "object" ? { ...(child as Record<string, unknown>) } : {};
    cursor = cursor[key] as Record<string, unknown>;
  });
  return next;
};

type FormInstance<T extends object = Record<string, unknown>> = {
  getFieldsValue: (_all?: boolean) => T;
  setFieldValue: (name: FieldName, value: unknown) => void;
  setFieldsValue: (values: Partial<T>) => void;
  resetFields: () => void;
};

const FormContext = createContext<FormInstance | null>(null);

function useForm<T extends object = Record<string, unknown>>(): [FormInstance<T>] {
  const [values, setValues] = useState<Record<string, unknown>>({});
  const valuesRef = useRef(values);
  valuesRef.current = values;
  const initialRef = useRef<Record<string, unknown>>({});

  const form = useMemo<FormInstance<T>>(
    () => ({
      getFieldsValue: () => valuesRef.current as T,
      setFieldValue: (name, value) => {
        setValues((current) => {
          const next = setIn(current, name, value);
          valuesRef.current = next;
          return next;
        });
      },
      setFieldsValue: (nextValues) => {
        setValues((current) => {
          const next = { ...current, ...(nextValues as Record<string, unknown>) };
          valuesRef.current = next;
          return next;
        });
      },
      resetFields: () => {
        setValues(initialRef.current);
        valuesRef.current = initialRef.current;
      },
    }),
    [],
  );

  (form as FormInstance & { __setInitial?: (values: Record<string, unknown>) => void }).__setInitial = (
    nextInitial,
  ) => {
    initialRef.current = nextInitial;
    setValues((current) => {
      const next = { ...nextInitial, ...current };
      valuesRef.current = next;
      return next;
    });
  };

  return [form];
}

type FormProps<T extends object> = {
  form?: FormInstance<any>;
  initialValues?: Partial<T>;
  onFinish?: (values: T) => void | Promise<void | unknown>;
  onValuesChange?: (changedValues: Partial<T>, values: T) => void;
  children?: ReactNode;
  layout?: "vertical" | "horizontal";
  style?: CSSProperties;
};

function FormRoot<T extends object = Record<string, unknown>>({
  form: providedForm,
  initialValues,
  onFinish,
  children,
  layout = "vertical",
  style,
}: FormProps<T>) {
  const [fallbackForm] = useForm<T>();
  const form = providedForm ?? fallbackForm;
  const initializedRef = useRef(false);

  useEffect(() => {
    if (initialValues && !initializedRef.current) {
      initializedRef.current = true;
      (form as FormInstance & { __setInitial?: (values: Record<string, unknown>) => void }).__setInitial?.(
        initialValues as Record<string, unknown>,
      );
    }
  }, [form, initialValues]);

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    void onFinish?.(form.getFieldsValue(true));
  };

  return (
    <FormContext.Provider value={form as FormInstance}>
      <form className={cx("bc-form", `bc-form--${layout}`)} style={style} onSubmit={handleSubmit}>
        {children}
      </form>
    </FormContext.Provider>
  );
}

type FormItemProps = {
  name?: FieldName;
  label?: ReactNode;
  children?: ReactNode;
  rules?: Array<{ required?: boolean; message?: string }>;
  initialValue?: unknown;
};

const FormItem = ({ name, label, children, initialValue }: FormItemProps) => {
  const form = useContext(FormContext);
  const id = name ? `field-${toPath(name).join("-")}` : undefined;

  useEffect(() => {
    if (form && name && initialValue !== undefined && getIn(form.getFieldsValue(true), name) === undefined) {
      form.setFieldValue(name, initialValue);
    }
  }, [form, initialValue, name]);

  let control = children;
  if (form && name && isValidElement(children)) {
    const child = children as ReactElement<Record<string, unknown>>;
    const value = getIn(form.getFieldsValue(true), name);
    control = cloneElement(child, {
      id,
      value: value ?? "",
      onChange: (next: unknown) => {
        (child.props as { onChange?: (value: unknown) => void }).onChange?.(next);
        const normalized =
          next && typeof next === "object" && "target" in next
            ? (next as { target: { value: unknown } }).target.value
            : next;
        form.setFieldValue(name, normalized === "" ? undefined : normalized);
      },
    });
  }

  const Wrapper = name ? "label" : "div";

  return (
    <Wrapper className="bc-form-item" htmlFor={name ? id : undefined}>
      {label ? <span className="bc-form-label">{label}</span> : null}
      {control}
    </Wrapper>
  );
};

export const Form = Object.assign(FormRoot, { Item: FormItem, useForm });

export const Button = AppButton;
export const Select = AppSelect;

export const Input = Object.assign(TextInput, {
  TextArea,
  Search: ({
    onSearch,
    enterButton,
    loading,
    size: _size,
    ...props
  }: Omit<InputHTMLAttributes<HTMLInputElement>, "size"> & {
    onSearch?: (value: string) => void;
    enterButton?: ReactNode;
    loading?: boolean;
    size?: "small" | "middle" | "large";
  }) => {
    const [value, setValue] = useState(String(props.value ?? props.defaultValue ?? ""));
    return (
      <div className="bc-search-input">
        <TextInput
          {...props}
          value={value}
          onChange={(event) => {
            setValue(event.target.value);
            props.onChange?.(event);
          }}
          onKeyDown={(event) => {
            props.onKeyDown?.(event);
            if (event.key === "Enter") onSearch?.(value);
          }}
        />
        <Button type="primary" loading={loading} onClick={() => onSearch?.(value)}>
          {enterButton || "搜索"}
        </Button>
      </div>
    );
  },
});

export const InputNumber = ({
  value,
  onChange,
  min,
  max,
  precision,
  ...props
}: Omit<InputHTMLAttributes<HTMLInputElement>, "onChange" | "value"> & {
  value?: number | string;
  onChange?: (value: number | undefined) => void;
  min?: number;
  max?: number;
  precision?: number;
}) => (
  <TextInput
    {...props}
    type="number"
    value={value ?? ""}
    min={min}
    max={max}
    step={precision === 0 ? 1 : undefined}
    onChange={(event) => {
      const next = event.target.value === "" ? undefined : Number(event.target.value);
      onChange?.(next);
    }}
  />
);

export const Typography = {
  Title: ({ level = 1, children, style, className }: { level?: 1 | 2 | 3 | 4 | 5; children: ReactNode; style?: CSSProperties; className?: string }) => {
    const TagName = `h${level}` as keyof JSX.IntrinsicElements;
    return <TagName className={cx("bc-title", className)} style={style}>{children}</TagName>;
  },
  Paragraph: ({ children, type, style, className }: { children: ReactNode; type?: string; style?: CSSProperties; className?: string; ellipsis?: unknown; code?: boolean }) => (
    <p className={cx("bc-paragraph", type === "secondary" && "bc-text--secondary", className)} style={style}>{children}</p>
  ),
  Text: ({
    children,
    type,
    strong,
    style,
    className,
    code,
    italic,
  }: {
    children: ReactNode;
    type?: "secondary" | "danger";
    strong?: boolean;
    style?: CSSProperties;
    className?: string;
    code?: boolean;
    italic?: boolean;
  }) => (
    <span
      className={cx(
        "bc-text",
        type === "secondary" && "bc-text--secondary",
        type === "danger" && "bc-text--danger",
        strong && "bc-text--strong",
        code && "bc-text--code",
        italic && "bc-text--italic",
        className,
      )}
      style={style}
    >
      {children}
    </span>
  ),
};

export const Space = ({
  children,
  direction = "horizontal",
  size = 8,
  wrap,
  align,
  style,
  className,
}: {
  children?: ReactNode;
  direction?: "horizontal" | "vertical";
  size?: number | "small" | "middle" | "large" | [number, number];
  wrap?: boolean;
  align?: CSSProperties["alignItems"];
  style?: CSSProperties;
  className?: string;
}) => {
  const gap = Array.isArray(size) ? `${size[1]}px ${size[0]}px` : typeof size === "number" ? size : size === "large" ? 18 : size === "middle" ? 14 : 8;
  return (
    <div
      className={cx("bc-space", direction === "vertical" && "bc-space--vertical", wrap && "bc-space--wrap", className)}
      style={{ gap, alignItems: align, ...style }}
    >
      {children}
    </div>
  );
};

Space.Compact = ({ children, style }: { children: ReactNode; style?: CSSProperties }) => (
  <div className="bc-space bc-space--compact" style={style}>{children}</div>
);

export const Card = ({
  title,
  extra,
  children,
  style,
  className,
  onClick,
  "data-testid": testId,
  loading,
}: {
  title?: ReactNode;
  extra?: ReactNode;
  children?: ReactNode;
  style?: CSSProperties;
  className?: string;
  onClick?: () => void;
  size?: "small";
  bordered?: boolean;
  variant?: string;
  hoverable?: boolean;
  styles?: unknown;
  loading?: boolean;
  "data-testid"?: string;
}) => (
  <section className={cx("bc-card", className)} style={style} onClick={onClick} data-testid={testId}>
    {title || extra ? (
      <div className="bc-card-header">
        <div>{title}</div>
        {extra ? <div>{extra}</div> : null}
      </div>
    ) : null}
    <div className="bc-card-body">{loading ? <Skeleton active paragraph={{ rows: 3 }} /> : children}</div>
  </section>
);

export const Tag = ({ children, color, style, onClick }: { children: ReactNode; color?: string; style?: CSSProperties; onClick?: () => void }) => {
  const tone = color === "green" || color === "success" ? "success" : color === "red" || color === "error" ? "danger" : color === "gold" || color === "orange" || color === "warning" ? "warning" : color === "blue" || color === "processing" ? "info" : "neutral";
  return <span className={cx("bc-badge", `bc-badge--${tone}`)} style={style} onClick={onClick}>{children}</span>;
};

export const Empty = Object.assign(
  ({ description }: { description?: ReactNode; image?: unknown; style?: CSSProperties }) => (
    <EmptyState description={typeof description === "string" ? description : "暂无数据"} />
  ),
  { PRESENTED_IMAGE_SIMPLE: "simple" },
);

export const Spin = ({ size }: { size?: string }) => <Spinner label={size === "small" ? "加载中" : "加载中"} />;

export const Divider = ({ style, children }: { style?: CSSProperties; children?: ReactNode; orientation?: string; plain?: boolean }) => (
  <div className="bc-divider-wrap" style={style}>
    <hr className="bc-divider" />
    {children ? <span>{children}</span> : null}
  </div>
);

export const Alert = ({
  message,
  description,
  type = "info",
  style,
}: {
  message?: ReactNode;
  description?: ReactNode;
  type?: "info" | "success" | "warning" | "error";
  showIcon?: boolean;
  style?: CSSProperties;
}) => (
  <div className={cx("bc-alert", `bc-alert--${type}`)} style={style}>
    {message ? <div className="bc-alert-title">{message}</div> : null}
    {description ? <div className="bc-alert-description">{description}</div> : null}
  </div>
);

export const Skeleton = ({ paragraph, style }: { active?: boolean; title?: unknown; paragraph?: { rows?: number }; style?: CSSProperties }) => (
  <div className="bc-skeleton" aria-label="加载中" style={style}>
    <span />
    {Array.from({ length: paragraph?.rows ?? 3 }).map((_, index) => <span key={index} />)}
  </div>
);

export const Layout = Object.assign(
  ({ children, style }: { children: ReactNode; style?: CSSProperties }) => <div className="bc-layout" style={style}>{children}</div>,
  {
    Header: ({ children, style }: { children: ReactNode; style?: CSSProperties }) => <header className="bc-layout-header" style={style}>{children}</header>,
    Content: ({ children, style }: { children: ReactNode; style?: CSSProperties }) => <main className="bc-layout-content" style={style}>{children}</main>,
    Footer: ({ children, style }: { children: ReactNode; style?: CSSProperties }) => <footer className="bc-layout-footer" style={style}>{children}</footer>,
  },
);

export const Row = ({ children, gutter, style }: { children: ReactNode; gutter?: number | [number, number]; style?: CSSProperties }) => {
  const gap = Array.isArray(gutter) ? `${gutter[1]}px ${gutter[0]}px` : gutter ?? 16;
  return <div className="bc-row" style={{ gap, ...style }}>{children}</div>;
};

export const Col = ({ children }: { children: ReactNode; xs?: number; sm?: number; lg?: number }) => (
  <div className="bc-col">{children}</div>
);

export const Statistic = ({ title, value, prefix, valueStyle }: { title: ReactNode; value: ReactNode; prefix?: ReactNode; valueStyle?: CSSProperties }) => (
  <div className="bc-statistic">
    <div className="bc-statistic-title">{title}</div>
    <div className="bc-statistic-value" style={valueStyle}>{prefix}{value}</div>
  </div>
);

export type ColumnsType<T> = Array<{
  title: ReactNode;
  dataIndex?: keyof T | string;
  key?: string;
  width?: number;
  ellipsis?: boolean;
  render?: (value: any, record: T, index: number) => ReactNode;
}>;

export const Table = <T extends any>({
  columns,
  dataSource,
  rowKey = "key",
  loading,
}: {
  columns: ColumnsType<T>;
  dataSource: T[];
  rowKey?: keyof T | string;
  loading?: boolean;
  pagination?: { pageSize?: number } | false;
  size?: string;
  scroll?: unknown;
  style?: CSSProperties;
}) => (
  <div className="bc-table-wrap">
    {loading ? <div className="bc-table-loading"><Spinner /></div> : null}
    <table className="bc-table">
      <thead>
        <tr>{columns.map((column) => <th key={column.key ?? String(column.dataIndex)}>{column.title}</th>)}</tr>
      </thead>
      <tbody>
        {dataSource.map((record, rowIndex) => (
          <tr key={String((record as Record<string, unknown>)[String(rowKey)] ?? rowIndex)}>
            {columns.map((column) => {
              const value = column.dataIndex ? (record as Record<string, unknown>)[String(column.dataIndex)] : undefined;
              return <td key={column.key ?? String(column.dataIndex)}>{column.render ? column.render(value, record, rowIndex) : String(value ?? "")}</td>;
            })}
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);

const ListItem = ({ children, style, onClick, actions }: { children: ReactNode; style?: CSSProperties; onClick?: () => void; actions?: ReactNode[] }) => (
  <li className="bc-list-item" style={style} onClick={onClick}>
    <div className="bc-list-item-main">{children}</div>
    {actions?.length ? <div className="bc-list-actions">{actions}</div> : null}
  </li>
);

ListItem.Meta = ({ title, description, avatar }: { title?: ReactNode; description?: ReactNode; avatar?: ReactNode }) => (
  <div className="bc-list-meta">
    {avatar ? <div>{avatar}</div> : null}
    {title ? <div className="bc-list-title">{title}</div> : null}
    {description ? <div className="bc-list-description">{description}</div> : null}
  </div>
);

export const List = Object.assign(
  <T,>({ dataSource, renderItem, children, style, loading, header }: { dataSource?: T[]; renderItem?: (item: T, index: number) => ReactNode; children?: ReactNode; style?: CSSProperties; loading?: boolean; size?: string; locale?: unknown; header?: ReactNode }) => (
    <ul className="bc-list" style={style}>
      {header ? <li className="bc-list-header">{header}</li> : null}
      {loading ? <li className="bc-list-item"><Spinner /></li> : null}
      {dataSource && renderItem ? dataSource.map(renderItem) : children}
    </ul>
  ),
  { Item: ListItem },
);

export const Collapse = ({ items, defaultActiveKey }: { bordered?: boolean; size?: string; ghost?: boolean; defaultActiveKey?: string[]; items: Array<{ key: string; label: ReactNode; children: ReactNode }> }) => (
  <Accordion.Root className="bc-collapse" type="multiple" defaultValue={defaultActiveKey ?? items.map((item) => item.key)}>
    {items.map((item) => (
      <Accordion.Item className="bc-collapse-item" key={item.key} value={item.key}>
        <Accordion.Header>
          <Accordion.Trigger className="bc-collapse-trigger">{item.label}</Accordion.Trigger>
        </Accordion.Header>
        <Accordion.Content className="bc-collapse-content">{item.children}</Accordion.Content>
      </Accordion.Item>
    ))}
  </Accordion.Root>
);

export const Drawer = ({ open, onClose, title, children, width, footer }: { open: boolean; onClose: () => void; title?: ReactNode; children: ReactNode; width?: number; placement?: string; footer?: ReactNode }) => (
  <Dialog.Root open={open} onOpenChange={(nextOpen) => !nextOpen && onClose()}>
    <Dialog.Portal>
      <Dialog.Overlay className="bc-drawer-overlay" />
      <Dialog.Content className="bc-drawer-content" style={{ width }}>
        <div className="bc-drawer-header">
          <Dialog.Title className="bc-dialog-title">{title}</Dialog.Title>
          <Dialog.Close className="bc-dialog-close" aria-label="关闭抽屉"><Cross1Icon /></Dialog.Close>
        </div>
        <div className="bc-drawer-body">{children}</div>
        {footer ? <div className="bc-drawer-footer">{footer}</div> : null}
      </Dialog.Content>
    </Dialog.Portal>
  </Dialog.Root>
);

export const Tooltip = ({ title, children }: { title?: ReactNode; children: ReactNode; placement?: string }) => (
  <TooltipPrimitive.Provider delayDuration={200}>
    <TooltipPrimitive.Root>
      <TooltipPrimitive.Trigger asChild>{children}</TooltipPrimitive.Trigger>
      <TooltipPrimitive.Portal>
        <TooltipPrimitive.Content className="bc-tooltip" sideOffset={6}>{title}</TooltipPrimitive.Content>
      </TooltipPrimitive.Portal>
    </TooltipPrimitive.Root>
  </TooltipPrimitive.Provider>
);

export const Radio = Object.assign(
  () => null,
  {
    Group: ({ value, onChange, children, "aria-label": ariaLabel }: { value: string; onChange: (event: { target: { value: string } }) => void; children: ReactNode; disabled?: boolean; "aria-label"?: string; id?: string }) => (
      <RadioPrimitive.Root className="bc-radio-group" value={value} onValueChange={(nextValue) => onChange({ target: { value: nextValue } })} aria-label={ariaLabel}>
        {children}
      </RadioPrimitive.Root>
    ),
    Button: ({ value, children }: { value: string; children: ReactNode }) => (
      <RadioPrimitive.Item className="bc-radio-button" value={value}>
        {children}
      </RadioPrimitive.Item>
    ),
  },
);

export const Descriptions = Object.assign(
  ({ children, style }: { children: ReactNode; column?: unknown; bordered?: boolean; size?: string; style?: CSSProperties; styles?: unknown }) => (
    <dl className="bc-descriptions" style={style}>{children}</dl>
  ),
  {
    Item: ({ label, children }: { label: ReactNode; children: ReactNode }) => (
      <div className="bc-description-item">
        <dt>{label}</dt>
        <dd>{children}</dd>
      </div>
    ),
  },
);

export const Timeline = ({ items }: { items: Array<{ children: ReactNode; color?: string }> }) => (
  <ol className="bc-timeline">
    {items.map((item, index) => <li key={index}>{item.children}</li>)}
  </ol>
);

export const ConfigProvider = ({ children }: { children: ReactNode; locale?: unknown; theme?: unknown }) => <>{children}</>;

export const message = {
  success: (text: string) => console.info(text),
  info: (text: string) => console.info(text),
  error: (text: string) => console.error(text),
  warning: (text: string) => console.warn(text),
};

export const Breadcrumb = ({ items, style }: { items: Array<{ title: ReactNode }>; style?: CSSProperties }) => (
  <nav className="bc-breadcrumb" style={style}>{items.map((item, index) => <span key={index}>{item.title}</span>)}</nav>
);

export const Result = ({ title, subTitle, extra, status }: { title: ReactNode; subTitle?: ReactNode; extra?: ReactNode; status?: string }) => (
  <div className={cx("bc-result", status === "warning" && "bc-result--warning")}>
    <h2>{title}</h2>
    {subTitle ? <p>{subTitle}</p> : null}
    {extra}
  </div>
);

export const AutoComplete = ({ options, value, onSelect, onSearch, onChange, children, placeholder, style }: { options?: SelectOption[]; value?: string; onSelect?: (value: string) => void; onSearch?: (value: string) => void; onChange?: (value: string) => void; children?: ReactNode; placeholder?: string; style?: CSSProperties; allowClear?: boolean }) => (
  <div className="bc-autocomplete">
    {children && isValidElement(children)
      ? cloneElement(children as ReactElement<any>, {
          value,
          onChange: (event: React.ChangeEvent<HTMLInputElement>) => onSearch?.(event.target.value),
          list: "bc-autocomplete-options",
        })
      : (
        <TextInput
          value={value}
          placeholder={placeholder}
          style={style}
          list="bc-autocomplete-options"
          onChange={(event) => {
            onChange?.(event.target.value);
            onSearch?.(event.target.value);
          }}
          onBlur={() => value && onSelect?.(value)}
        />
      )}
    <datalist id="bc-autocomplete-options">
      {options?.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
    </datalist>
  </div>
);

export const Steps = ({ items, current = 0, style }: { items: Array<{ title: ReactNode; description?: ReactNode; status?: string }>; current?: number; size?: string; direction?: string; style?: CSSProperties }) => (
  <ol className="bc-steps" style={style}>
    {items.map((item, index) => (
      <li key={index} data-active={index <= current}>
        <span>{index + 1}</span>
        <div>
          <strong>{item.title}</strong>
          {item.description ? <small>{item.description}</small> : null}
        </div>
      </li>
    ))}
  </ol>
);
